"""Train all 29 event models for Fix3, preserving tuned hyperparameters from Fix1b."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from tqdm import tqdm

from models import split_by_season, train_one_event

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Tuned hyperparameters from Fix1b — preserved for retraining on new labels
TUNED_PARAMS = {
    "any_big_six_hitter": {"reg_alpha": 0, "reg_lambda": 1.0, "max_depth": 4},
    "match_runs_gte_300": {"reg_alpha": 0, "reg_lambda": 0.5, "max_depth": 3},
    "any_four_wicket_haul": {"reg_alpha": 0, "reg_lambda": 0.5, "max_depth": 3},
    "team_has_top_scorer": {"reg_alpha": 0.1, "reg_lambda": 5.0, "max_depth": 4},
}


def main() -> None:
    np.random.seed(42)

    print("Loading data...")
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    features = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    labels = pd.read_parquet(PROCESSED_DIR / "labels.parquet")
    catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")

    splits = split_by_season(matches)
    for name, ids in splits.items():
        print(f"  {name}: {len(ids)} matches")

    records = []
    for _, ev in tqdm(catalog.iterrows(), total=len(catalog), desc="Training events"):
        event_id = ev["event_id"]
        xgb_params = TUNED_PARAMS.get(event_id)
        result = train_one_event(
            event_id, catalog, labels, features, matches, splits, xgb_params=xgb_params
        )

        # Persist model
        joblib.dump(result["model"], MODELS_DIR / f"{event_id}.joblib")

        records.append(
            {
                "event_id": event_id,
                "category": ev["category"],
                "scope": ev["scope"],
                "train_base_rate": result["train_base_rate"],
                "val_logloss": result["val_metrics"].get("log_loss", np.nan),
                "val_brier": result["val_metrics"].get("brier", np.nan),
                "val_logloss_baseline": result["val_metrics"].get(
                    "log_loss_baseline", np.nan
                ),
                "val_beats_baseline": result["val_metrics"]
                .get("log_loss_vs_baseline", -np.inf)
                > 0,
                "test_logloss": result["test_metrics"].get("log_loss", np.nan),
                "test_brier": result["test_metrics"].get("brier", np.nan),
                "test_logloss_baseline": result["test_metrics"].get(
                    "log_loss_baseline", np.nan
                ),
                "test_beats_baseline": result["test_metrics"]
                .get("log_loss_vs_baseline", -np.inf)
                > 0,
                "n_train": result["n_train"],
                "n_val": result["n_val"],
                "n_test": result["n_test"],
                "status": result["status"],
            }
        )

    metrics_df = pd.DataFrame(records)
    metrics_df.to_parquet(PROCESSED_DIR / "metrics.parquet", index=False)

    print("\n" + "=" * 70)
    print("Summary — sorted by test improvement over baseline")
    print("=" * 70)
    summary = metrics_df.copy()
    summary["test_improvement"] = summary["test_logloss_baseline"] - summary["test_logloss"]
    summary = summary.sort_values("test_improvement", ascending=False)
    print(
        summary[
            [
                "event_id",
                "test_logloss",
                "test_logloss_baseline",
                "test_beats_baseline",
                "status",
            ]
        ].to_string(index=False)
    )
    print("=" * 70)
    n_beat = summary["test_beats_baseline"].sum()
    print(f"Models beating baseline on test: {int(n_beat)} / {len(summary)}")


if __name__ == "__main__":
    main()
