"""Training utilities for IPL predictor — one calibrated model per event."""

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Time-aware splits
# ---------------------------------------------------------------------------

TIME_SPLITS = {
    "train": [
        "2007/08", "2009", "2009/10", "2011", "2012", "2013", "2014",
        "2015", "2016", "2017", "2018", "2019", "2020/21", "2021",
    ],
    "val": ["2022", "2023"],
    "test": ["2024", "2025", "2026"],
}


def split_by_season(matches_df: pd.DataFrame) -> dict[str, list[str]]:
    """Return match_id lists for train/val/test based on season strings."""
    return {
        split_name: matches_df[matches_df["season"].isin(seasons)]["match_id"].tolist()
        for split_name, seasons in TIME_SPLITS.items()
    }


# ---------------------------------------------------------------------------
# Training-matrix builder (handles team-scope swapping)
# ---------------------------------------------------------------------------


def build_training_matrix(
    event_id: str,
    catalog_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    features_df: pd.DataFrame,
    match_ids: list[str],
) -> tuple[pd.DataFrame, pd.Series, np.ndarray]:
    """Return X, y, match_ids for a single event, filtered to the given match_ids.

    For team-scope events, rows where team == team2 have all t1_ / t2_ features
    swapped so that the team-under-prediction always sits in the t1_ slot.
    """
    scope = catalog_df[catalog_df["event_id"] == event_id]["scope"].iloc[0]

    event_labels = labels_df[
        (labels_df["event_id"] == event_id) & (labels_df["match_id"].isin(match_ids))
    ].copy()
    event_labels = event_labels.dropna(subset=["outcome"])

    if event_labels.empty:
        return pd.DataFrame(), pd.Series(dtype=int), np.array([], dtype=str)

    merged = event_labels.merge(features_df, on="match_id", how="left")

    if scope == "team":
        # Swap t1_ ↔ t2_ for every row where the team-under-prediction is team2
        swap_mask = merged["team"] == merged["team2"]
        if swap_mask.any():
            swap_map: dict[str, str] = {}
            for col in merged.columns:
                if col.startswith("t1_"):
                    target = "t2_" + col[3:]
                    if target in merged.columns:
                        swap_map[col] = target
                elif col.startswith("t2_"):
                    target = "t1_" + col[3:]
                    if target in merged.columns:
                        swap_map[col] = target
                elif "_t1_" in col:
                    target = col.replace("_t1_", "_t2_", 1)
                    if target in merged.columns:
                        swap_map[col] = target
                elif "_t2_" in col:
                    target = col.replace("_t2_", "_t1_", 1)
                    if target in merged.columns:
                        swap_map[col] = target

            if swap_map:
                swapped = merged.loc[swap_mask].rename(columns=swap_map)
                # Re-align column order so .values assignment is safe
                swapped = swapped[merged.columns]
                merged.loc[swap_mask, :] = swapped.values

            # Negate t1-vs-t2 diff features since their components were swapped
            for col in merged.columns:
                if col.startswith("t1_vs_t2_"):
                    merged.loc[swap_mask, col] = -merged.loc[swap_mask, col]

    y = merged["outcome"].astype(int)
    match_ids_out = merged["match_id"].values

    meta_cols = ["match_id", "event_id", "team", "outcome", "team1", "team2"]
    drop_cols = [c for c in meta_cols if c in merged.columns]
    X = merged.drop(columns=drop_cols)

    return X, y, match_ids_out


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def evaluate(model, X: pd.DataFrame, y: pd.Series, base_rate: float) -> dict:
    """Compute log-loss, Brier, and baseline comparisons."""
    n = len(y)
    if n == 0:
        return {
            "log_loss": np.nan,
            "brier": np.nan,
            "log_loss_baseline": np.nan,
            "brier_baseline": np.nan,
            "base_rate": base_rate,
            "n": 0,
            "positive_rate": np.nan,
            "log_loss_vs_baseline": np.nan,
            "brier_vs_baseline": np.nan,
        }

    probs = model.predict_proba(X)[:, 1]
    positive_rate = y.mean()
    baseline_probs = np.full(n, base_rate)

    if len(np.unique(y)) <= 1:
        # All labels are the same — log_loss is undefined, Brier reduces to MSE of a constant
        ll = np.nan
        brier = float(np.mean((y - probs) ** 2))
        ll_baseline = np.nan
        brier_baseline = float(np.mean((y - baseline_probs) ** 2)) if n > 0 else np.nan
    else:
        ll = log_loss(y, probs)
        brier = brier_score_loss(y, probs)
        ll_baseline = log_loss(y, baseline_probs)
        brier_baseline = brier_score_loss(y, baseline_probs)

    return {
        "log_loss": ll,
        "brier": brier,
        "log_loss_baseline": ll_baseline,
        "brier_baseline": brier_baseline,
        "base_rate": base_rate,
        "n": n,
        "positive_rate": positive_rate,
        "log_loss_vs_baseline": ll_baseline - ll,
        "brier_vs_baseline": brier_baseline - brier,
    }


# ---------------------------------------------------------------------------
# Per-event training
# ---------------------------------------------------------------------------


def train_one_event(
    event_id: str,
    catalog_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    features_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    splits: dict[str, list[str]],
    xgb_params: dict | None = None,
) -> dict:
    """Train (or baseline) one model for a single event.

    Optional xgb_params overrides the default XGBClassifier hyperparameters.
    """
    # Inject team1/team2 into features so the swap logic has them available
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
    train_base_rate = float(y_train.mean()) if n_train > 0 else np.nan

    n_pos = int(y_train.sum()) if n_train > 0 else 0
    n_neg = n_train - n_pos

    if n_pos < 30 or n_neg < 30:
        model = DummyClassifier(strategy="prior")
        if n_train > 0:
            model.fit(X_train, y_train)
        status = "INSUFFICIENT DATA"
    else:
        default_params = {
            "n_estimators": 300,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "eval_metric": "logloss",
            "random_state": 42,
            "n_jobs": -1,
        }
        if xgb_params:
            default_params.update(xgb_params)

        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
                (
                    "xgb",
                    CalibratedClassifierCV(
                        estimator=XGBClassifier(**default_params),
                        method="isotonic",
                        cv=StratifiedKFold(
                            n_splits=3, shuffle=True, random_state=42
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
