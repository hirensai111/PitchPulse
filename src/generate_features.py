"""Generate features.parquet from parsed match and ball data."""

import random
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from features import build_feature_row, precompute_all

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def main() -> None:
    print("Loading data...")
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    balls = pd.read_parquet(PROCESSED_DIR / "balls.parquet")

    matches = matches.sort_values("date").reset_index(drop=True)

    print("Pre-computing aggregate tables...")
    precomputed = precompute_all(matches, balls)

    print("Building feature rows...")
    rows = []
    for _, match_row in tqdm(matches.iterrows(), total=len(matches)):
        row = build_feature_row(match_row, matches, balls, **precomputed)
        rows.append(row)

    features_df = pd.DataFrame(rows)
    cols = ["match_id"] + [c for c in features_df.columns if c != "match_id"]
    features_df = features_df[cols]

    # Leakage self-test
    print("\nRunning leakage self-test...")
    random.seed(42)
    test_idx = random.randint(0, len(matches) - 1)
    test_match = matches.iloc[test_idx]
    test_date = test_match["date"]
    test_match_id = test_match["match_id"]

    trunc_matches = matches[matches["date"] < test_date].copy()
    trunc_balls = balls[balls["match_id"].isin(trunc_matches["match_id"])].copy()

    if not trunc_matches.empty:
        trunc_precomputed = precompute_all(trunc_matches, trunc_balls)
        test_row_trunc = build_feature_row(
            test_match, trunc_matches, trunc_balls, **trunc_precomputed
        )
        full_row = features_df[features_df["match_id"] == test_match_id].iloc[0].to_dict()

        del test_row_trunc["match_id"]
        del full_row["match_id"]

        mismatches = []
        for k in test_row_trunc:
            v1 = test_row_trunc[k]
            v2 = full_row[k]
            if isinstance(v1, float) and isinstance(v2, float):
                if abs(v1 - v2) > 1e-6:
                    mismatches.append((k, v1, v2))
            elif v1 != v2:
                mismatches.append((k, v1, v2))

        if mismatches:
            print("LEAKAGE DETECTED!")
            for k, v1, v2 in mismatches[:10]:
                print(f"  {k}: truncated={v1}, full={v2}")
            raise ValueError("Leakage detected in feature computation")
        else:
            print("Leakage check passed")
    else:
        print("Skipping leakage test (first match)")

    features_df.to_parquet(PROCESSED_DIR / "features.parquet", index=False)
    print(
        f"\nWrote {len(features_df)} rows × {len(features_df.columns)} columns to features.parquet"
    )


if __name__ == "__main__":
    main()
