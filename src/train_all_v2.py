"""Retrain all 29 models with sigmoid calibration (Fix A)."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from models import build_training_matrix, evaluate, split_by_season

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models_v2"


def train_one_event_v2(
    event_id: str,
    catalog_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    features_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    splits: dict,
) -> dict:
    """Train one model with sigmoid calibration and cv=5."""
    features_with_teams = features_df.merge(
        matches_df[["match_id", "team1", "team2"]], on="match_id", how="left"
    )

    X_train, y_train, _ = build_training_matrix(
        event_id, catalog_df, labels_df, features_with_teams, splits["train"]
    )
    X_val, y_val, _ = build_training_matrix(
        event_id, catalog_df, labels_df, features_with_teams, splits["val"]
    )
    X_test, y_test, _ = build_training_matrix(
        event_id, catalog_df, labels_df, features_with_teams, splits["test"]
    )

    n_train = len(y_train)
    n_val = len(y_val)
    n_test = len(y_test)
    train_base_rate = float(y_train.mean()) if n_train > 0 else float("nan")
    n_pos = int(y_train.sum()) if n_train > 0 else 0
    n_neg = n_train - n_pos

    if n_pos < 30 or n_neg < 30:
        model = DummyClassifier(strategy="prior")
        if n_train > 0:
            model.fit(X_train, y_train)
        status = "INSUFFICIENT DATA"
    else:
        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
                (
                    "xgb",
                    CalibratedClassifierCV(
                        estimator=XGBClassifier(
                            n_estimators=300,
                            max_depth=4,
                            learning_rate=0.05,
                            subsample=0.8,
                            colsample_bytree=0.8,
                            eval_metric="logloss",
                            random_state=42,
                            n_jobs=-1,
                        ),
                        method="sigmoid",
                        cv=StratifiedKFold(
                            n_splits=5, shuffle=True, random_state=42
                        ),
                    ),
                ),
            ]
        )
        model.fit(X_train, y_train)
        status = "trained"

    val_metrics = evaluate(model, X_val, y_val, train_base_rate) if n_val > 0 else {}
    test_metrics = evaluate(model, X_test, y_test, train_base_rate) if n_test > 0 else {}

    return {
        "model": model,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "n_train": n_train,
        "n_val": n_val,
        "n_test": n_test,
        "train_base_rate": train_base_rate,
        "status": status,
    }


def main() -> None:
    print("Loading data...")
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    features = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    labels = pd.read_parquet(PROCESSED_DIR / "labels.parquet")
    catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")

    splits = split_by_season(matches)
    print(f"  train: {len(splits['train'])} matches")
    print(f"  val:   {len(splits['val'])} matches")
    print(f"  test:  {len(splits['test'])} matches")

    all_metrics = []
    for _, ev in catalog.iterrows():
        event_id = ev["event_id"]
        print(f"\nTraining {event_id} ...")
        result = train_one_event_v2(
            event_id, catalog, labels, features, matches, splits
        )

        model = result["model"]
        joblib.dump(model, MODELS_DIR / f"{event_id}.joblib")

        vm = result["val_metrics"]
        tm = result["test_metrics"]
        all_metrics.append({
            "event_id": event_id,
            "status": result["status"],
            "n_train": result["n_train"],
            "n_val": result["n_val"],
            "n_test": result["n_test"],
            "train_base_rate": result["train_base_rate"],
            "val_logloss": vm.get("log_loss", float("nan")),
            "val_brier": vm.get("brier", float("nan")),
            "test_logloss": tm.get("log_loss", float("nan")),
            "test_brier": tm.get("brier", float("nan")),
            "test_logloss_baseline": tm.get("log_loss_baseline", float("nan")),
            "test_brier_baseline": tm.get("brier_baseline", float("nan")),
            "test_beats_baseline": tm.get("log_loss", float("inf")) < tm.get("log_loss_baseline", float("inf")) if tm else False,
        })
        print(f"  test LL: {tm.get('log_loss', 'N/A')}, baseline: {tm.get('log_loss_baseline', 'N/A')}")

    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_parquet(PROCESSED_DIR / "metrics_v2.parquet", index=False)

    print("\n" + "="*60)
    print("Summary (sorted by test improvement over baseline)")
    print("="*60)
    metrics_df["improvement"] = metrics_df["test_logloss_baseline"] - metrics_df["test_logloss"]
    print(metrics_df.sort_values("improvement", ascending=False)[[
        "event_id", "test_logloss", "test_logloss_baseline", "test_beats_baseline", "status"
    ]].to_string(index=False))
    beats = metrics_df["test_beats_baseline"].sum()
    print(f"\nModels beating baseline on test: {beats} / {len(metrics_df)}")


if __name__ == "__main__":
    main()
