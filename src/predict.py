"""Prediction interface for IPL predictor — rank events by likelihood & notability."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from features import build_feature_row, precompute_all

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def _infer_season(date: pd.Timestamp) -> str:
    """Map a date to the IPL season string used in the dataset."""
    year = date.year
    if year == 2008:
        return "2007/08"
    if year == 2010:
        return "2009/10"
    if year == 2021:
        return "2020/21"
    return str(year)


def _swap_features(row: pd.Series) -> pd.Series:
    """Swap t1_ ↔ t2_ in a feature row (for team2 prediction)."""
    swap_map: dict[str, str] = {}
    for col in row.index:
        if col.startswith("t1_"):
            swap_map[col] = "t2_" + col[3:]
        elif col.startswith("t2_"):
            swap_map[col] = "t1_" + col[3:]
        elif "_t1_" in col:
            swap_map[col] = col.replace("_t1_", "_t2_", 1)
        elif "_t2_" in col:
            swap_map[col] = col.replace("_t2_", "_t1_", 1)
    return row.rename(swap_map).reindex(row.index)


def predict_match(
    team1: str,
    team2: str,
    venue: str,
    match_date: str,
    models_dir: str = "models",
    mmr_lambda: float = 0.5,
    use_mmr: bool = True,
) -> dict:
    """Return ranked event predictions for a single future match.

    Outputs:
      - meta: all 29 events with probabilities, base rates, and lifts
      - top_5_likely: top 5 by raw probability (with optional MMR diversity penalty)
      - top_5_notable: top 5 by lift over base rate (with optional MMR diversity penalty)
    """
    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    balls = pd.read_parquet(PROCESSED_DIR / "balls.parquet")
    catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")
    metrics = pd.read_parquet(PROCESSED_DIR / "metrics.parquet")

    base_rates = dict(zip(metrics["event_id"], metrics["train_base_rate"]))

    # ------------------------------------------------------------------
    # Build feature row for the synthetic match
    # ------------------------------------------------------------------
    date = pd.Timestamp(match_date)
    season = _infer_season(date)
    match_id = f"predict_{match_date}_{team1[:3].upper()}_v_{team2[:3].upper()}"

    match_row = pd.Series({
        "match_id": match_id,
        "team1": team1,
        "team2": team2,
        "venue": venue,
        "date": date,
        "season": season,
        "city": None,
    })

    precomputed = precompute_all(matches, balls)
    features_dict = build_feature_row(match_row, matches, balls, **precomputed)
    features_df = pd.DataFrame([features_dict])

    # Attach team1/team2 for swap logic
    features_df["team1"] = team1
    features_df["team2"] = team2

    # ------------------------------------------------------------------
    # Score every event
    # ------------------------------------------------------------------
    models_path = Path(models_dir)
    all_scores: list[dict] = []

    for _, ev in catalog.iterrows():
        event_id = ev["event_id"]
        scope = ev["scope"]
        category = ev["category"]
        description = ev["description"]

        model_path = models_path / f"{event_id}.joblib"
        if not model_path.exists():
            continue

        model = joblib.load(model_path)

        if scope == "match":
            X = features_df.drop(columns=["match_id", "team1", "team2"], errors="ignore")
            prob = float(model.predict_proba(X)[0, 1])
            base_rate = base_rates.get(event_id, 0.5)
            lift = prob / base_rate if base_rate > 0 else np.inf
            all_scores.append({
                "event_id": event_id,
                "display_name": description,
                "category": category,
                "scope": scope,
                "team": None,
                "probability": prob,
                "base_rate": base_rate,
                "lift": lift,
            })
        else:  # team scope — predict for both teams
            for team in (team1, team2):
                if team == team2:
                    # Swap so the team-under-prediction sits in t1_ slot
                    row = features_df.iloc[0].copy()
                    row = _swap_features(row)
                    X = row.drop(
                        index=["match_id", "team1", "team2"], errors="ignore"
                    ).to_frame().T
                else:
                    X = features_df.drop(
                        columns=["match_id", "team1", "team2"], errors="ignore"
                    )

                prob = float(model.predict_proba(X)[0, 1])
                base_rate = base_rates.get(event_id, 0.5)
                lift = prob / base_rate if base_rate > 0 else np.inf
                all_scores.append({
                    "event_id": event_id,
                    "display_name": description,
                    "category": category,
                    "scope": scope,
                    "team": team,
                    "probability": prob,
                    "base_rate": base_rate,
                    "lift": lift,
                })

    # ------------------------------------------------------------------
    # MMR diversity-ranked top-5
    # ------------------------------------------------------------------
    def _mmr_rank(items: list[dict], score_key: str, lambda_param: float = 0.5) -> list[dict]:
        """Greedy MMR: pick highest score, then downweight same-category items."""
        remaining = [dict(it) for it in items]
        selected: list[dict] = []
        selected_cats: set[str] = set()

        while len(selected) < 5 and remaining:
            # Adjust scores based on category overlap with already-selected
            best_idx = -1
            best_score = -np.inf
            for idx, it in enumerate(remaining):
                score = it[score_key]
                if it["category"] in selected_cats:
                    score *= lambda_param
                if score > best_score:
                    best_score = score
                    best_idx = idx

            picked = remaining.pop(best_idx)
            selected_cats.add(picked["category"])
            selected.append(picked)

        return selected

    if use_mmr:
        top_5_likely = _mmr_rank(all_scores, "probability", lambda_param=mmr_lambda)
        top_5_notable = _mmr_rank(all_scores, "lift", lambda_param=mmr_lambda)
    else:
        top_5_likely = sorted(all_scores, key=lambda x: x["probability"], reverse=True)[:5]
        top_5_notable = sorted(all_scores, key=lambda x: x["lift"], reverse=True)[:5]

    return {
        "meta": {
            "team1": team1,
            "team2": team2,
            "venue": venue,
            "match_date": match_date,
            "season": season,
        },
        "all_probabilities": all_scores,
        "top_5_likely": top_5_likely,
        "top_5_notable": top_5_notable,
    }


if __name__ == "__main__":
    import json

    result = predict_match(
        team1="Chennai Super Kings",
        team2="Mumbai Indians",
        venue="M A Chidambaram Stadium",
        match_date="2026-05-01",
    )
    print(json.dumps(result["top_5_likely"], indent=2))
    print("\n--- NOTABLE ---\n")
    print(json.dumps(result["top_5_notable"], indent=2))
