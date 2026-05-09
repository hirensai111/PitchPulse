"""Check feature importance of home/away features across top 10 models."""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from models import build_training_matrix, split_by_season

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

# Load data
matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
features = pd.read_parquet(PROCESSED_DIR / "features.parquet")
labels = pd.read_parquet(PROCESSED_DIR / "labels.parquet")
catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")
metrics = pd.read_parquet(PROCESSED_DIR / "metrics.parquet")

features_with_teams = features.merge(
    matches[["match_id", "team1", "team2"]], on="match_id", how="left"
)
splits = split_by_season(matches)

# Get top 10 models by margin
metrics["margin"] = metrics["test_logloss_baseline"] - metrics["test_logloss"]
top10 = metrics.sort_values("margin", ascending=False).head(10)

# Get feature names from one event's training matrix
event_id = top10.iloc[0]["event_id"]
X_sample, _, _ = build_training_matrix(
    event_id, catalog, labels, features_with_teams, splits["train"]
)
feature_names = list(X_sample.columns)
print(f"Feature count: {len(feature_names)}")

TARGET_FEATURES = ["is_home_game_t1", "t1_home_win_rate", "is_neutral_venue"]
for tf in TARGET_FEATURES:
    if tf in feature_names:
        idx = feature_names.index(tf)
        print(f"  {tf} -> index {idx}")
    else:
        print(f"  {tf} -> NOT FOUND")

print()

# Collect importances
importances = {tf: [] for tf in TARGET_FEATURES}

for _, row in top10.iterrows():
    ev = row["event_id"]
    model_path = MODELS_DIR / f"{ev}.joblib"
    if not model_path.exists():
        continue
    
    model = joblib.load(model_path)
    cal = model.named_steps["xgb"]
    
    # Average importances across the 3 calibrated classifiers
    imp_sum = np.zeros(len(feature_names))
    for cc in cal.calibrated_classifiers_:
        imp_sum += cc.estimator.feature_importances_
    avg_imp = imp_sum / len(cal.calibrated_classifiers_)
    
    for tf in TARGET_FEATURES:
        if tf in feature_names:
            idx = feature_names.index(tf)
            importances[tf].append(avg_imp[idx])

print("=" * 60)
print("FEATURE IMPORTANCE ANALYSIS (top 10 models)")
print("=" * 60)
for tf in TARGET_FEATURES:
    vals = importances[tf]
    if vals:
        print(f"{tf:30s}: mean={np.mean(vals):.5f}, std={np.std(vals):.5f}, min={np.min(vals):.5f}, max={np.max(vals):.5f}")
    else:
        print(f"{tf:30s}: NO DATA")

# Also show what fraction of total importance these represent
total_importance = np.zeros(len(feature_names))
count = 0
for _, row in top10.iterrows():
    ev = row["event_id"]
    model_path = MODELS_DIR / f"{ev}.joblib"
    if not model_path.exists():
        continue
    model = joblib.load(model_path)
    cal = model.named_steps["xgb"]
    for cc in cal.calibrated_classifiers_:
        total_importance += cc.estimator.feature_importances_
        count += 1
total_importance /= count

print()
print("Top 20 most important features (mean across top 10 models):")
sorted_idx = np.argsort(total_importance)[::-1]
for i in range(20):
    idx = sorted_idx[i]
    print(f"  {i+1:2d}. {feature_names[idx]:40s} {total_importance[idx]:.5f}")

print()
print("Home/away feature ranks:")
for tf in TARGET_FEATURES:
    if tf in feature_names:
        idx = feature_names.index(tf)
        rank = list(sorted_idx).index(idx) + 1
        print(f"  {tf:30s}: rank={rank:3d}, importance={total_importance[idx]:.5f}")
