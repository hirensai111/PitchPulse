"""Generate event labels from parsed CricSheet data."""

from pathlib import Path

import pandas as pd
from tqdm import tqdm

from events import EVENT_CATALOG, compute_labels_for_match

# Resolve paths relative to project root (this file is in src/)
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def main() -> None:
    print("Loading matches and balls...")
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    balls = pd.read_parquet(PROCESSED_DIR / "balls.parquet")

    # Group balls by match_id once
    balls_by_match = dict(tuple(balls.groupby("match_id")))

    all_labels = []
    for _, match_row in tqdm(matches.iterrows(), total=len(matches), desc="Computing labels"):
        match_id = match_row["match_id"]
        match_balls = balls_by_match.get(match_id, pd.DataFrame())
        all_labels.extend(compute_labels_for_match(match_row, match_balls))

    labels_df = pd.DataFrame(all_labels)

    # Enforce dtypes
    labels_df["outcome"] = labels_df["outcome"].astype("Int8")

    # Write catalog
    catalog_df = pd.DataFrame(EVENT_CATALOG)
    catalog_df.to_parquet(PROCESSED_DIR / "events_catalog.parquet", index=False)

    # Write labels
    labels_df.to_parquet(PROCESSED_DIR / "labels.parquet", index=False)

    # Summary
    total = len(labels_df)
    na_count = labels_df["outcome"].isna().sum()
    unique_events = labels_df["event_id"].nunique()
    print(f"\nWrote {total:,} label rows ({unique_events} unique events)")
    print(f"NA outcomes: {na_count:,} ({na_count / total:.2%})")


if __name__ == "__main__":
    main()
