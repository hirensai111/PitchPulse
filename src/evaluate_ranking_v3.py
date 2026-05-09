"""Step 5c evaluation: compare blended notability score vs pure lift."""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from models import split_by_season
from predict_v2 import _apply_mmr

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def load_models(catalog: pd.DataFrame, models_dir: Path):
    models = {}
    for _, ev in catalog.iterrows():
        event_id = ev["event_id"]
        path = models_dir / f"{event_id}.joblib"
        if not path.exists():
            continue
        models[event_id] = joblib.load(path)
    return models


def get_actual(match_id: str, labels_df: pd.DataFrame, catalog_df: pd.DataFrame) -> set[str]:
    match_labels = labels_df[labels_df["match_id"] == match_id]
    actual = set()
    for _, ev in catalog_df.iterrows():
        event_id = ev["event_id"]
        scope = ev["scope"]
        ev_labels = match_labels[match_labels["event_id"] == event_id]
        for _, row in ev_labels.iterrows():
            if pd.notna(row["outcome"]) and row["outcome"] == 1:
                key = f'{event_id}:{row["team"]}' if scope == "team" else event_id
                actual.add(key)
    return actual


def predict_for_match(match_id: str, catalog_df, models, features_with_teams, base_rates):
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
            notability_score = (prob ** 0.3) * lift if base_rate > 0 else 0.0
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
                "notability_score": notability_score,
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
                notability_score = (prob ** 0.3) * lift if base_rate > 0 else 0.0
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
                    "notability_score": notability_score,
                })
    return scores


def hits_at_k(pred_keys, actual_keys, k=5):
    return len(set(pred_keys[:k]) & set(actual_keys))


def jaccard(list_a, list_b):
    sa, sb = set(list_a), set(list_b)
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union > 0 else 0.0


def rank_notable(scores, method, mmr_lambda=None):
    """Rank notable list. method: 'lift', 'blended', or 'naive'."""
    if method == "naive":
        return sorted(scores, key=lambda x: x["base_rate"], reverse=True)[:5]
    elif method == "lift":
        if mmr_lambda is not None:
            return _apply_mmr(scores, "lift", mmr_lambda)
        return sorted(scores, key=lambda x: x["lift"], reverse=True)[:5]
    elif method == "blended":
        if mmr_lambda is not None:
            return _apply_mmr(scores, "notability_score", mmr_lambda)
        return sorted(scores, key=lambda x: x["notability_score"], reverse=True)[:5]
    else:
        raise ValueError(f"Unknown method: {method}")


def rank_likely(scores, mmr_lambda=None):
    if mmr_lambda is not None:
        return _apply_mmr(scores, "probability", mmr_lambda)
    return sorted(scores, key=lambda x: x["probability"], reverse=True)[:5]


def evaluate():
    print("Loading data ...")
    matches = pd.read_parquet(PROCESSED_DIR / "matches.parquet")
    labels = pd.read_parquet(PROCESSED_DIR / "labels.parquet")
    catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")
    features = pd.read_parquet(PROCESSED_DIR / "features.parquet")
    metrics = pd.read_parquet(PROCESSED_DIR / "metrics.parquet")

    base_rates = dict(zip(metrics["event_id"], metrics["train_base_rate"]))
    splits = split_by_season(matches)
    test_match_ids = splits["test"]

    features_with_teams = features.merge(
        matches[["match_id", "team1", "team2"]], on="match_id", how="left"
    )

    models = load_models(catalog, MODELS_DIR)
    print(f"Loaded {len(models)} models")

    # Storage for all predictions
    all_preds = []

    print(f"Evaluating {len(test_match_ids)} test matches ...")
    for i, match_id in enumerate(test_match_ids):
        if i % 20 == 0:
            print(f"  {i}/{len(test_match_ids)} ...")

        scores = predict_for_match(match_id, catalog, models, features_with_teams, base_rates)
        actual = get_actual(match_id, labels, catalog)

        if not scores or not actual:
            continue

        pred = {
            "match_id": match_id,
            "actual": actual,
            "likely_mmr": [s["key"] for s in rank_likely(scores, mmr_lambda=0.3)],
            "notable_lift_mmr": [s["key"] for s in rank_notable(scores, "lift", mmr_lambda=0.3)],
            "notable_blended_mmr": [s["key"] for s in rank_notable(scores, "blended", mmr_lambda=0.3)],
            "notable_naive": [s["key"] for s in rank_notable(scores, "naive")],
        }
        all_preds.append(pred)

    n = len(all_preds)
    print(f"\nValid matches: {n}")

    # ------------------------------------------------------------------
    # Per-slot hit rates (notable)
    # ------------------------------------------------------------------
    methods = ["notable_lift_mmr", "notable_blended_mmr"]
    slot_hits = {m: {i: [] for i in range(5)} for m in methods}

    for p in all_preds:
        for m in methods:
            keys = p[m]
            for slot in range(5):
                if slot < len(keys):
                    slot_hits[m][slot].append(1 if keys[slot] in p["actual"] else 0)

    print("\n" + "=" * 80)
    print("PER-SLOT HIT RATE (notable)")
    print("=" * 80)
    for m in methods:
        label = "OLD (lift)" if "lift" in m else "NEW (blended)"
        print(f"\n{label}:")
        for slot in range(5):
            hits = slot_hits[m][slot]
            rate = np.mean(hits) if hits else 0.0
            print(f"  Slot {slot + 1}: {rate:.3f}  (n={len(hits)})")

    # ------------------------------------------------------------------
    # Precision@K
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PRECISION@K")
    print("=" * 80)

    methods_full = {
        "notable_lift_mmr": "notable (lift)",
        "notable_blended_mmr": "notable (blended)",
        "likely_mmr": "likely",
        "notable_naive": "naive baseline",
    }

    for key, label in methods_full.items():
        print(f"\n{label}:")
        for k in range(1, 6):
            vals = []
            for p in all_preds:
                vals.append(hits_at_k(p[key], p["actual"], k) / k)
            print(f"  P@{k}: {np.mean(vals):.3f}")

    # ------------------------------------------------------------------
    # Hits@5
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("HITS@5")
    print("=" * 80)
    for key, label in methods_full.items():
        vals = [hits_at_k(p[key], p["actual"], 5) for p in all_preds]
        print(f"  {label:<25s}: {np.mean(vals):.3f}  (std={np.std(vals):.3f})")

    # ------------------------------------------------------------------
    # Likely vs Notable Jaccard overlap
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("LIKELY vs NOTABLE JACCARD OVERLAP")
    print("=" * 80)
    for notable_key in ["notable_lift_mmr", "notable_blended_mmr"]:
        label = "OLD (lift)" if "lift" in notable_key else "NEW (blended)"
        jacs = [jaccard(p["likely_mmr"], p[notable_key]) for p in all_preds]
        print(f"  {label}: {np.mean(jacs):.3f}")

    # ------------------------------------------------------------------
    # Side-by-side demo on 5 diverse matches
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SIDE-BY-SIDE DEMO: 5 TEST MATCHES")
    print("=" * 80)

    # Pick 5 diverse matches
    np.random.seed(42)
    demo_ids = np.random.choice([p["match_id"] for p in all_preds], size=5, replace=False)

    for match_id in demo_ids:
        match_row = matches[matches["match_id"] == match_id].iloc[0]
        scores = predict_for_match(match_id, catalog, models, features_with_teams, base_rates)
        actual = get_actual(match_id, labels, catalog)

        print(f"\n{'-'*80}")
        print(f"MATCH: {match_row['team1']} vs {match_row['team2']} | {match_row['date']} | {match_id}")
        print(f"Actual events: {len(actual)}")
        print('-'*80)

        # Old notable (lift)
        old_notable = rank_notable(scores, "lift", mmr_lambda=0.3)
        print("\nOLD NOTABLE (lift-ranked):")
        for i, s in enumerate(old_notable, 1):
            ok = "OK" if s["key"] in actual else "MISS"
            name = s["display_name"][:50].encode("ascii", "replace").decode("ascii")
            print(f"  {i}. {name:<50s} prob={s['probability']:.3f} lift={s['lift']:.2f} | {ok}")

        # New notable (blended)
        new_notable = rank_notable(scores, "blended", mmr_lambda=0.3)
        print("\nNEW NOTABLE (blended-ranked):")
        for i, s in enumerate(new_notable, 1):
            ok = "OK" if s["key"] in actual else "MISS"
            name = s["display_name"][:50].encode("ascii", "replace").decode("ascii")
            print(f"  {i}. {name:<50s} prob={s['probability']:.3f} lift={s['lift']:.2f} notab={s['notability_score']:.3f} | {ok}")

        # Likely for comparison
        likely = rank_likely(scores, mmr_lambda=0.3)
        print("\nLIKELY (MMR lambda=0.3):")
        for i, s in enumerate(likely, 1):
            ok = "OK" if s["key"] in actual else "MISS"
            name = s["display_name"][:50].encode("ascii", "replace").decode("ascii")
            print(f"  {i}. {name:<50s} prob={s['probability']:.3f} | {ok}")

    return all_preds


if __name__ == "__main__":
    evaluate()
