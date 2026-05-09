"""Part 3 re-evaluation: compare ranking strategies on test set."""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from models import build_training_matrix, evaluate, split_by_season
from predict_v2 import _apply_mmr

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def _load_models(catalog: pd.DataFrame, models_dir: Path):
    """Load all models."""
    models = {}
    for _, ev in catalog.iterrows():
        event_id = ev["event_id"]
        path = models_dir / f"{event_id}.joblib"
        if not path.exists():
            continue
        models[event_id] = joblib.load(path)
    return models


def _get_actual_outcomes_for_match(match_id: str, labels_df: pd.DataFrame, catalog_df: pd.DataFrame) -> list[str]:
    """Return actual event keys that occurred for a given match."""
    match_labels = labels_df[labels_df["match_id"] == match_id]
    actual = []
    for _, ev in catalog_df.iterrows():
        event_id = ev["event_id"]
        scope = ev["scope"]
        ev_labels = match_labels[match_labels["event_id"] == event_id]
        if ev_labels.empty:
            continue
        for _, row in ev_labels.iterrows():
            if pd.notna(row["outcome"]) and row["outcome"] == 1:
                key = f"{event_id}:{row['team']}" if scope == "team" else event_id
                actual.append(key)
    return actual


def _predict_all_events_for_match(
    match_id: str,
    catalog_df: pd.DataFrame,
    models: dict,
    features_with_teams: pd.DataFrame,
    base_rates: dict,
) -> list[dict]:
    """Return scored events for a single match."""
    match_features = features_with_teams[features_with_teams["match_id"] == match_id]
    if match_features.empty:
        return []

    row = match_features.iloc[0]
    team1 = row["team1"]
    team2 = row["team2"]

    scores = []
    for _, ev in catalog_df.iterrows():
        event_id = ev["event_id"]
        scope = ev["scope"]
        category = ev["category"]
        description = ev["description"]

        model = models.get(event_id)
        if model is None:
            continue

        if scope == "match":
            X = pd.DataFrame([row.drop(labels=["match_id", "team1", "team2"], errors="ignore")])
            prob = float(model.predict_proba(X)[0, 1])
            base_rate = base_rates.get(event_id, 0.5)
            lift = prob / base_rate if base_rate > 0 else np.inf
            scores.append({
                "key": event_id,
                "event_id": event_id,
                "display_name": description,
                "category": category,
                "scope": scope,
                "team": None,
                "probability": prob,
                "base_rate": base_rate,
                "lift": lift,
            })
        else:
            for team in (team1, team2):
                if team == team2:
                    swap_map = {}
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
                    swapped_row = row.rename(swap_map).reindex(row.index)
                    for col in swapped_row.index:
                        if col.startswith("t1_vs_t2_"):
                            swapped_row[col] = -swapped_row[col]
                    X = pd.DataFrame([swapped_row.drop(labels=["match_id", "team1", "team2"], errors="ignore")])
                else:
                    X = pd.DataFrame([row.drop(labels=["match_id", "team1", "team2"], errors="ignore")])

                prob = float(model.predict_proba(X)[0, 1])
                base_rate = base_rates.get(event_id, 0.5)
                lift = prob / base_rate if base_rate > 0 else np.inf
                key = f"{event_id}:{team}"
                scores.append({
                    "key": key,
                    "event_id": event_id,
                    "display_name": description,
                    "category": category,
                    "scope": scope,
                    "team": team,
                    "probability": prob,
                    "base_rate": base_rate,
                    "lift": lift,
                })
    return scores


def _rank_by_strategy(scores: list[dict], strategy: str) -> tuple[list[dict], list[dict]]:
    """Return (top_5_likely, top_5_notable) for a strategy."""
    if strategy == "no_mmr":
        likely = sorted(scores, key=lambda x: x["probability"], reverse=True)[:5]
        notable = sorted(scores, key=lambda x: x["lift"], reverse=True)[:5]
    elif strategy == "mmr_0.3":
        likely = _apply_mmr(scores, "probability", 0.3)
        notable = _apply_mmr(scores, "lift", 0.3)
    elif strategy == "mmr_0.5":
        likely = _apply_mmr(scores, "probability", 0.5)
        notable = _apply_mmr(scores, "lift", 0.5)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    return likely, notable


def _hits_at_k(predicted_keys: list[str], actual_keys: list[str], k: int = 5) -> int:
    return len(set(predicted_keys[:k]) & set(actual_keys))


def _jaccard(list_a: list[str], list_b: list[str]) -> float:
    set_a, set_b = set(list_a), set(list_b)
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0


def evaluate_strategies():
    """Run full Part 3 evaluation."""
    print("Loading data ...")
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    labels = pd.read_parquet(PROCESSED_DIR / "labels.parquet")
    catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")
    features = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    metrics = pd.read_parquet(PROCESSED_DIR / "metrics.parquet")

    # Use metrics_v2 if available
    metrics_v2_path = PROCESSED_DIR / "metrics_v2.parquet"
    if metrics_v2_path.exists():
        metrics = pd.read_parquet(metrics_v2_path)

    base_rates = dict(zip(metrics["event_id"], metrics["train_base_rate"]))

    splits = split_by_season(matches)
    test_match_ids = splits["test"]

    features_with_teams = features.merge(
        matches[["match_id", "team1", "team2"]], on="match_id", how="left"
    )

    models = _load_models(catalog, MODELS_DIR)
    print(f"Loaded {len(models)} models from {MODELS_DIR}")

    strategies = ["no_mmr", "mmr_0.3", "mmr_0.5"]

    # Store predictions per match per strategy
    match_predictions = []

    print(f"Evaluating {len(test_match_ids)} test matches ...")
    for i, match_id in enumerate(test_match_ids):
        if i % 20 == 0:
            print(f"  {i}/{len(test_match_ids)} ...")

        scores = _predict_all_events_for_match(match_id, catalog, models, features_with_teams, base_rates)
        actual = _get_actual_outcomes_for_match(match_id, labels, catalog)

        if not scores or not actual:
            continue

        preds = {"match_id": match_id, "actual": actual, "strategies": {}}
        for strategy in strategies:
            likely, notable = _rank_by_strategy(scores, strategy)
            preds["strategies"][strategy] = {
                "likely_keys": [s["key"] for s in likely],
                "notable_keys": [s["key"] for s in notable],
            }
        match_predictions.append(preds)

    # ------------------------------------------------------------------
    # Compute metrics
    # ------------------------------------------------------------------
    results = {s: {"likely_hits": [], "notable_hits": [], "likely_jaccard": [], "notable_jaccard": []} for s in strategies}
    slot_hits = {s: {"likely": {i: [] for i in range(5)}, "notable": {i: [] for i in range(5)}} for s in strategies}
    precision_k = {s: {"likely": {k: [] for k in range(1, 6)}, "notable": {k: [] for k in range(1, 6)}} for s in strategies}

    for preds in match_predictions:
        actual = preds["actual"]
        for strategy in strategies:
            lk = preds["strategies"][strategy]["likely_keys"]
            nk = preds["strategies"][strategy]["notable_keys"]

            results[strategy]["likely_hits"].append(_hits_at_k(lk, actual, 5))
            results[strategy]["notable_hits"].append(_hits_at_k(nk, actual, 5))
            results[strategy]["likely_jaccard"].append(_jaccard(lk, actual))
            results[strategy]["notable_jaccard"].append(_jaccard(nk, actual))

            for slot in range(5):
                if slot < len(lk):
                    slot_hits[strategy]["likely"][slot].append(1 if lk[slot] in actual else 0)
                if slot < len(nk):
                    slot_hits[strategy]["notable"][slot].append(1 if nk[slot] in actual else 0)

            for k in range(1, 6):
                precision_k[strategy]["likely"][k].append(_hits_at_k(lk, actual, k) / k)
                precision_k[strategy]["notable"][k].append(_hits_at_k(nk, actual, k) / k)

    # ------------------------------------------------------------------
    # Print summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PART 3: RANKING STRATEGY COMPARISON")
    print("=" * 80)

    for strategy in strategies:
        lh = results[strategy]["likely_hits"]
        nh = results[strategy]["notable_hits"]
        lj = results[strategy]["likely_jaccard"]
        nj = results[strategy]["notable_jaccard"]

        print(f"\n--- {strategy} ---")
        print(f"Matches evaluated: {len(lh)}")
        print(f"Likely   hits@5: {np.mean(lh):.3f}  (std={np.std(lh):.3f})")
        print(f"Notable  hits@5: {np.mean(nh):.3f}  (std={np.std(nh):.3f})")
        print(f"Likely   Jaccard: {np.mean(lj):.3f}")
        print(f"Notable  Jaccard: {np.mean(nj):.3f}")

    # Per-slot hit rates
    print("\n" + "-" * 80)
    print("PER-SLOT HIT RATE (notable)")
    print("-" * 80)
    for strategy in strategies:
        print(f"\n{strategy}:")
        for slot in range(5):
            hits = slot_hits[strategy]["notable"][slot]
            rate = np.mean(hits) if hits else 0.0
            print(f"  Slot {slot + 1}: {rate:.3f}  (n={len(hits)})")

    # Precision@K
    print("\n" + "-" * 80)
    print("PRECISION@K")
    print("-" * 80)
    for strategy in strategies:
        print(f"\n{strategy}:")
        for k in [1, 2, 3, 4, 5]:
            pl = np.mean(precision_k[strategy]["likely"][k])
            pn = np.mean(precision_k[strategy]["notable"][k])
            print(f"  P@{k} likely={pl:.3f} notable={pn:.3f}")

    return results, slot_hits, precision_k, match_predictions


if __name__ == "__main__":
    evaluate_strategies()
