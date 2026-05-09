"""Prediction interface v2 — adaptive MMR with multiple ranking strategies."""

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
            target = "t2_" + col[3:]
            if target in row.index:
                swap_map[col] = target
        elif col.startswith("t2_"):
            target = "t1_" + col[3:]
            if target in row.index:
                swap_map[col] = target
        elif "_t1_" in col:
            target = col.replace("_t1_", "_t2_", 1)
            if target in row.index:
                swap_map[col] = target
        elif "_t2_" in col:
            target = col.replace("_t2_", "_t1_", 1)
            if target in row.index:
                swap_map[col] = target
    row = row.rename(swap_map).reindex(row.index)
    # Negate t1-vs-t2 diff features since their components were swapped
    for col in row.index:
        if col.startswith("t1_vs_t2_"):
            row[col] = -row[col]
    return row


def _apply_mmr(items: list[dict], score_key: str, lambda_param: float) -> list[dict]:
    """Greedy MMR: pick highest score, then downweight same-category items."""
    remaining = [dict(it) for it in items]
    selected: list[dict] = []
    selected_cats: set[str] = set()

    while len(selected) < 5 and remaining:
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


def _rank_by_strategy(
    all_scores: list[dict], strategy: str
) -> tuple[list[dict], list[dict]]:
    """Return (top_5_likely, top_5_notable) for a given strategy string.

    Strategies:
      - "no_mmr"   : raw probability / notability_score ranking
      - "mmr_0.3"  : MMR with λ=0.3
      - "mmr_0.5"  : MMR with λ=0.5

    Notable list is ranked by blended notability_score = probability * lift,
    which balances "how likely" with "how surprising".
    """
    if strategy == "no_mmr":
        likely = sorted(all_scores, key=lambda x: x["probability"], reverse=True)[:5]
        notable = sorted(all_scores, key=lambda x: x["notability_score"], reverse=True)[:5]
    elif strategy == "mmr_0.3":
        likely = _apply_mmr(all_scores, "probability", 0.3)
        notable = _apply_mmr(all_scores, "notability_score", 0.3)
    elif strategy == "mmr_0.5":
        likely = _apply_mmr(all_scores, "probability", 0.5)
        notable = _apply_mmr(all_scores, "notability_score", 0.5)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    return likely, notable


def predict_match(
    team1: str,
    team2: str,
    venue: str,
    match_date: str,
    models_dir: str | None = None,
    metrics_file: str | None = None,
    precomputed: dict | None = None,
    models: dict | None = None,
) -> dict:
    """Return ranked event predictions for a single future match.

    Computes all 29 event probabilities and returns three ranking variants:
      - no_mmr  : pure probability / lift ranking
      - mmr_0.3 : adaptive MMR with λ=0.3 (recommended)
      - mmr_0.5 : original MMR with λ=0.5

    Each variant contains top_5_likely and top_5_notable lists.
    """
    models_path = Path(models_dir) if models_dir else MODELS_DIR
    metrics_path = PROCESSED_DIR / metrics_file if metrics_file else PROCESSED_DIR / "metrics.parquet"

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    balls = pd.read_parquet(PROCESSED_DIR / "balls.parquet")
    catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")
    metrics = pd.read_parquet(metrics_path)

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

    if precomputed is None:
        precomputed = precompute_all(matches, balls)
    features_dict = build_feature_row(match_row, matches, balls, **precomputed)
    features_df = pd.DataFrame([features_dict])

    # Attach team1/team2 for swap logic
    features_df["team1"] = team1
    features_df["team2"] = team2

    # ------------------------------------------------------------------
    # Score every event
    # ------------------------------------------------------------------
    all_scores: list[dict] = []

    for _, ev in catalog.iterrows():
        event_id = ev["event_id"]
        scope = ev["scope"]
        category = ev["category"]
        description = ev["description"]

        if models is not None and event_id in models:
            model = models[event_id]
        else:
            model_path = models_path / f"{event_id}.joblib"
            if not model_path.exists():
                continue
            model = joblib.load(model_path)

        if scope == "match":
            X = features_df.drop(columns=["match_id", "team1", "team2"], errors="ignore")
            prob = float(model.predict_proba(X)[0, 1])
            base_rate = base_rates.get(event_id, 0.5)
            lift = prob / base_rate if base_rate > 0 else np.inf
            notability_score = (prob ** 0.3) * lift if base_rate > 0 else 0.0
            all_scores.append({
                "event_id": event_id,
                "display_name": description,
                "category": category,
                "scope": scope,
                "team": None,
                "probability": prob,
                "base_rate": base_rate,
                "lift": lift,
                "notability_score": notability_score,
            })
        else:  # team scope
            for team in (team1, team2):
                if team == team2:
                    row = features_df.iloc[0].copy()
                    row = _swap_features(row)
                    X = row.drop(index=["match_id", "team1", "team2"], errors="ignore").to_frame().T
                else:
                    X = features_df.drop(columns=["match_id", "team1", "team2"], errors="ignore")

                prob = float(model.predict_proba(X)[0, 1])
                base_rate = base_rates.get(event_id, 0.5)
                lift = prob / base_rate if base_rate > 0 else np.inf
                notability_score = (prob ** 0.3) * lift if base_rate > 0 else 0.0
                all_scores.append({
                    "event_id": event_id,
                    "display_name": description,
                    "category": category,
                    "scope": scope,
                    "team": team,
                    "probability": prob,
                    "base_rate": base_rate,
                    "lift": lift,
                    "notability_score": notability_score,
                })

    # ------------------------------------------------------------------
    # Build all three ranking variants
    # ------------------------------------------------------------------
    variants = {}
    for strategy in ("no_mmr", "mmr_0.3", "mmr_0.5"):
        likely, notable = _rank_by_strategy(all_scores, strategy)
        variants[strategy] = {
            "top_5_likely": likely,
            "top_5_notable": notable,
        }

    return {
        "meta": {
            "team1": team1,
            "team2": team2,
            "venue": venue,
            "match_date": match_date,
            "season": season,
        },
        "all_probabilities": all_scores,
        "variants": variants,
    }


if __name__ == "__main__":
    import json

    result = predict_match(
        team1="Chennai Super Kings",
        team2="Mumbai Indians",
        venue="M A Chidambaram Stadium",
        match_date="2026-05-01",
    )
    for strategy, preds in result["variants"].items():
        print(f"\n=== {strategy} ===")
        print("LIKELY:")
        for ev in preds["top_5_likely"]:
            print(f"  {ev['display_name']:<45} p={ev['probability']:.3f} lift={ev['lift']:.2f}")
        print("NOTABLE:")
        for ev in preds["top_5_notable"]:
            print(f"  {ev['display_name']:<45} p={ev['probability']:.3f} lift={ev['lift']:.2f}")
