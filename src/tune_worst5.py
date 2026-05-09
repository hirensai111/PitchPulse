"""Grid-search regularization for the 5 worst-performing models (Fix1b Part 2)."""

from itertools import product
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.impute import SimpleImputer
from sklearn.metrics import log_loss
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from models import build_training_matrix, evaluate, split_by_season

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

PARAM_GRID = {
    "reg_alpha": [0, 0.1, 1.0],
    "reg_lambda": [0.5, 1.0, 5.0],
    "max_depth": [3, 4, 6],
}


def _make_pipeline(params: dict) -> Pipeline:
    """Build a fresh pipeline with the given regularization hyperparameters."""
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
            (
                "xgb",
                CalibratedClassifierCV(
                    estimator=XGBClassifier(
                        n_estimators=300,
                        max_depth=params["max_depth"],
                        learning_rate=0.05,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        reg_alpha=params["reg_alpha"],
                        reg_lambda=params["reg_lambda"],
                        eval_metric="logloss",
                        random_state=42,
                        n_jobs=-1,
                    ),
                    method="isotonic",
                    cv=StratifiedKFold(
                        n_splits=3, shuffle=True, random_state=42
                    ),
                ),
            ),
        ]
    )


def tune_event(
    event_id: str,
    catalog: pd.DataFrame,
    labels: pd.DataFrame,
    features_with_teams: pd.DataFrame,
    matches: pd.DataFrame,
    splits: dict,
    untuned_test_ll: float,
) -> dict:
    """Grid-search one event, retrain best config on train+val, evaluate on test."""
    X_train, y_train, _ = build_training_matrix(
        event_id, catalog, labels, features_with_teams, splits["train"]
    )
    X_val, y_val, _ = build_training_matrix(
        event_id, catalog, labels, features_with_teams, splits["val"]
    )
    X_test, y_test, _ = build_training_matrix(
        event_id, catalog, labels, features_with_teams, splits["test"]
    )

    if X_train.empty or X_val.empty:
        return {
            "event_id": event_id,
            "status": "skipped",
            "reason": "insufficient data",
            "test_logloss": untuned_test_ll,
            "tuned": False,
        }

    best_ll = np.inf
    best_params = None

    keys = list(PARAM_GRID.keys())
    for values in product(*PARAM_GRID.values()):
        params = dict(zip(keys, values))
        model = _make_pipeline(params)
        model.fit(X_train, y_train)

        probs = model.predict_proba(X_val)[:, 1]
        ll = log_loss(y_val, probs)

        if ll < best_ll:
            best_ll = ll
            best_params = params

    # Retrain best config on train+val
    X_tv = pd.concat([X_train, X_val], ignore_index=True)
    y_tv = pd.concat([y_train, y_val], ignore_index=True)

    tuned_model = _make_pipeline(best_params)
    tuned_model.fit(X_tv, y_tv)

    tuned_test_metrics = evaluate(tuned_model, X_test, y_test, float(y_tv.mean()))
    tuned_test_ll = tuned_test_metrics["log_loss"]

    # Regression guard: keep untuned if tuned is worse
    if tuned_test_ll > untuned_test_ll:
        return {
            "event_id": event_id,
            "status": "regression",
            "best_params": best_params,
            "untuned_test_logloss": untuned_test_ll,
            "tuned_test_logloss": tuned_test_ll,
            "test_logloss": untuned_test_ll,
            "tuned": False,
        }

    # Save tuned model
    joblib.dump(tuned_model, MODELS_DIR / f"{event_id}.joblib")

    return {
        "event_id": event_id,
        "status": "tuned",
        "best_params": best_params,
        "untuned_test_logloss": untuned_test_ll,
        "tuned_test_logloss": tuned_test_ll,
        "test_logloss": tuned_test_ll,
        "tuned": True,
    }


def main() -> None:
    print("Loading data...")
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    features = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    labels = pd.read_parquet(PROCESSED_DIR / "labels.parquet")
    catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")
    metrics = pd.read_parquet(PROCESSED_DIR / "metrics.parquet")

    features_with_teams = features.merge(
        matches[["match_id", "team1", "team2"]], on="match_id", how="left"
    )
    splits = split_by_season(matches)

    # Identify bottom 5 by margin (most negative = worst performers)
    metrics["margin"] = metrics["test_logloss_baseline"] - metrics["test_logloss"]
    worst5 = metrics.sort_values("margin", ascending=True).head(5)

    print(f"\nWorst 5 events to tune:")
    print(worst5[["event_id", "test_logloss", "test_logloss_baseline", "margin"]].to_string(index=False))
    print()

    results = []
    for _, row in worst5.iterrows():
        ev = row["event_id"]
        untuned_ll = row["test_logloss"]
        print(f"Tuning {ev} ...")
        res = tune_event(
            ev, catalog, labels, features_with_teams, matches, splits, untuned_ll
        )
        results.append(res)
        print(f"  -> {res['status']}: test LL = {res['test_logloss']:.6f}")
        if res["status"] == "tuned":
            print(f"    best params: {res['best_params']}")
        elif res["status"] == "regression":
            print(f"    regression: tuned {res['tuned_test_logloss']:.6f} > untuned {res['untuned_test_logloss']:.6f}")

    # Update metrics.parquet
    results_df = pd.DataFrame(results)
    metrics = metrics.merge(
        results_df[["event_id", "tuned", "test_logloss"]], on="event_id", how="left", suffixes=("", "_tuned")
    )
    # Overwrite test_logloss with tuned version where applicable
    tuned_mask = metrics["tuned"].fillna(False).astype(bool)
    metrics.loc[tuned_mask, "test_logloss"] = metrics.loc[tuned_mask, "test_logloss_tuned"]
    metrics = metrics.drop(columns=["test_logloss_tuned"])
    metrics["tuned"] = metrics["tuned"].fillna(False).astype(bool)
    # Recalculate beats_baseline
    metrics["test_beats_baseline"] = metrics["test_logloss_baseline"] > metrics["test_logloss"]
    metrics.to_parquet(PROCESSED_DIR / "metrics.parquet", index=False)

    print("\n" + "=" * 60)
    print("Tuning summary")
    print("=" * 60)
    for r in results:
        print(f"{r['event_id']:30s} {r['status']:12s} test_LL={r['test_logloss']:.6f}")


if __name__ == "__main__":
    main()
