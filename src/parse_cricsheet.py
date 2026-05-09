"""Parse CricSheet IPL JSON files into matches.parquet and balls.parquet."""

import json
import os
from pathlib import Path

import pandas as pd
from tqdm import tqdm

RAW_DIR = Path("ipl_json")
PROCESSED_DIR = Path("data/processed")


def parse_match(file_path: Path) -> tuple[dict, list[dict]]:
    """Parse a single CricSheet JSON file into match and ball records."""
    match_id = file_path.stem

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    info = data.get("info", {})

    # Dates: CricSheet stores a list; use the first (and usually only) date
    dates = info.get("dates", [])
    date = pd.to_datetime(dates[0]) if dates else pd.NaT

    # Teams
    teams = info.get("teams", [None, None])
    team1, team2 = teams[0], teams[1]

    # Toss
    toss = info.get("toss", {})
    toss_winner = toss.get("winner")
    toss_decision = toss.get("decision")

    # Outcome
    outcome = info.get("outcome", {})
    winner = outcome.get("winner")
    win_by_runs = None
    win_by_wickets = None
    result = None

    if "by" in outcome:
        by = outcome["by"]
        win_by_runs = by.get("runs")
        win_by_wickets = by.get("wickets")
    elif "eliminator" in outcome:
        winner = outcome["eliminator"]
        result = "tie"
    elif "result" in outcome:
        result = outcome["result"]  # e.g. "no result", "tie"

    # Player of match (can be missing)
    pom = info.get("player_of_match", [])
    player_of_match = pom[0] if pom else None

    match_record = {
        "match_id": match_id,
        "date": date,
        "season": info.get("season"),
        "venue": info.get("venue"),
        "city": info.get("city"),
        "team1": team1,
        "team2": team2,
        "toss_winner": toss_winner,
        "toss_decision": toss_decision,
        "winner": winner,
        "win_by_runs": win_by_runs,
        "win_by_wickets": win_by_wickets,
        "result": result,
        "player_of_match": player_of_match,
    }

    # Innings / ball-by-ball
    ball_records = []
    innings_list = data.get("innings", [])

    for innings_idx, innings in enumerate(innings_list, start=1):
        batting_team = innings.get("team")
        overs = innings.get("overs", [])

        for over_data in overs:
            over_num = over_data.get("over")
            deliveries = over_data.get("deliveries", [])

            for ball_idx, delivery in enumerate(deliveries, start=1):
                runs = delivery.get("runs", {})
                runs_batter = runs.get("batter", 0)
                runs_extras = runs.get("extras", 0)
                runs_total = runs.get("total", 0)

                # Extras type
                extras = delivery.get("extras", {})
                extras_type = None
                if extras:
                    # Take the first key present: wides, legbyes, noballs, byes, penalty
                    for key in ("wides", "legbyes", "noballs", "byes", "penalty"):
                        if key in extras:
                            extras_type = key
                            break

                # Wicket info
                wickets = delivery.get("wickets", [])
                is_wicket = len(wickets) > 0
                wicket_kind = None
                player_out = None
                if is_wicket:
                    w = wickets[0]
                    wicket_kind = w.get("kind")
                    player_out = w.get("player_out")

                ball_records.append(
                    {
                        "match_id": match_id,
                        "innings": innings_idx,
                        "batting_team": batting_team,
                        "over": over_num,
                        "ball": ball_idx,
                        "batter": delivery.get("batter"),
                        "non_striker": delivery.get("non_striker"),
                        "bowler": delivery.get("bowler"),
                        "runs_batter": runs_batter,
                        "runs_extras": runs_extras,
                        "runs_total": runs_total,
                        "is_wicket": is_wicket,
                        "wicket_kind": wicket_kind,
                        "player_out": player_out,
                        "extras_type": extras_type,
                    }
                )

    return match_record, ball_records


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    json_files = sorted(RAW_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {RAW_DIR.resolve()}")

    match_rows = []
    ball_rows = []
    skipped = []

    for file_path in tqdm(json_files, desc="Parsing matches"):
        try:
            match_rec, ball_recs = parse_match(file_path)
            match_rows.append(match_rec)
            ball_rows.extend(ball_recs)
        except Exception as e:
            skipped.append((file_path.name, str(e)))

    if skipped:
        print(f"\nSkipped {len(skipped)} file(s):")
        for name, err in skipped:
            print(f"  {name}: {err}")

    matches_df = pd.DataFrame(match_rows)
    balls_df = pd.DataFrame(ball_rows)

    # Sort matches by date
    matches_df = matches_df.sort_values("date", ignore_index=True)

    # Ensure consistent dtypes for Parquet
    matches_df["season"] = matches_df["season"].astype(str)
    matches_df["win_by_runs"] = pd.to_numeric(matches_df["win_by_runs"], errors="coerce").astype("Int64")
    matches_df["win_by_wickets"] = pd.to_numeric(matches_df["win_by_wickets"], errors="coerce").astype("Int64")
    matches_df["date"] = pd.to_datetime(matches_df["date"], errors="coerce")

    balls_df["innings"] = pd.to_numeric(balls_df["innings"], errors="coerce").astype("Int64")
    balls_df["over"] = pd.to_numeric(balls_df["over"], errors="coerce").astype("Int64")
    balls_df["ball"] = pd.to_numeric(balls_df["ball"], errors="coerce").astype("Int64")
    balls_df["runs_batter"] = pd.to_numeric(balls_df["runs_batter"], errors="coerce").astype("Int64")
    balls_df["runs_extras"] = pd.to_numeric(balls_df["runs_extras"], errors="coerce").astype("Int64")
    balls_df["runs_total"] = pd.to_numeric(balls_df["runs_total"], errors="coerce").astype("Int64")
    balls_df["is_wicket"] = balls_df["is_wicket"].astype(bool)

    # Write Parquet
    matches_path = PROCESSED_DIR / "matches.parquet"
    balls_path = PROCESSED_DIR / "balls.parquet"

    matches_df.to_parquet(matches_path, index=False)
    balls_df.to_parquet(balls_path, index=False)

    print(f"\nWrote {len(matches_df)} matches to {matches_path}")
    print(f"Wrote {len(balls_df)} deliveries to {balls_path}")


if __name__ == "__main__":
    main()
