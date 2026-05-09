"""Tune a single event given its event_id."""

import sys

from tune_top5 import tune_event
from models import split_by_season

import pandas as pd

from pathlib import Path

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def main():
    if len(sys.argv) < 2:
        print("Usage: python tune_one.py <event_id>")
        sys.exit(1)

    event_id = sys.argv[1]

    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    features = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    labels = pd.read_parquet(PROCESSED_DIR / "labels.parquet")
    catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")
    metrics = pd.read_parquet(PROCESSED_DIR / "metrics.parquet")

    features_with_teams = features.merge(
        matches[["match_id", "team1", "team2"]], on="match_id", how="left"
    )
    splits = split_by_season(matches)

    row = metrics[metrics["event_id"] == event_id].iloc[0]
    res = tune_event(
        event_id, catalog, labels, features_with_teams, matches, splits, row["test_logloss"]
    )
    print(res)


if __name__ == "__main__":
    main()
