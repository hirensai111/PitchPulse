"""Feature engineering library for IPL predictor — pure functions, no I/O."""

import numpy as np
import pandas as pd

from events import NON_BOWLER_WICKET_KINDS
from venue_mapping import get_home_team

# ---------------------------------------------------------------------------
# Pre-computation helpers (called once per generation run)
# ---------------------------------------------------------------------------


def precompute_all(matches_df: pd.DataFrame, balls_df: pd.DataFrame) -> dict:
    """Return dict of pre-computed aggregate tables for fast feature lookup."""
    return {
        "team_stats": _compute_team_stats(matches_df, balls_df),
        "player_bat_stats": _compute_player_bat_stats(matches_df, balls_df),
        "player_bowl_stats": _compute_player_bowl_stats(matches_df, balls_df),
    }


def _compute_team_stats(matches_df: pd.DataFrame, balls_df: pd.DataFrame) -> pd.DataFrame:
    balls_12 = balls_df[balls_df["innings"].isin([1, 2])]
    records = []

    for _, m in matches_df.iterrows():
        mid = m["match_id"]
        match_balls = balls_12[balls_12["match_id"] == mid]

        for team in (m["team1"], m["team2"]):
            team_balls = match_balls[match_balls["batting_team"] == team]
            opp_balls = match_balls[match_balls["batting_team"] != team]

            records.append(
                {
                    "match_id": mid,
                    "date": m["date"],
                    "team": team,
                    "venue": m["venue"],
                    "runs_scored": int(team_balls["runs_total"].sum()),
                    "runs_conceded": int(opp_balls["runs_total"].sum()),
                    "balls_faced": len(team_balls),
                    "balls_bowled": len(opp_balls),
                    "sixes_hit": int((team_balls["runs_batter"] == 6).sum()),
                    "sixes_conceded": int((opp_balls["runs_batter"] == 6).sum()),
                    "won": 1 if m["winner"] == team else 0,
                }
            )

    return pd.DataFrame(records)


def _compute_player_bat_stats(matches_df: pd.DataFrame, balls_df: pd.DataFrame) -> pd.DataFrame:
    balls_12 = balls_df[balls_df["innings"].isin([1, 2])]
    stats = (
        balls_12.groupby(["match_id", "batting_team", "batter"])
        .agg(
            runs=("runs_batter", "sum"),
            balls=("runs_batter", "count"),
            sixes=("runs_batter", lambda x: int((x == 6).sum())),
        )
        .reset_index()
    )
    stats = stats.rename(columns={"batting_team": "team"})
    stats = stats.merge(matches_df[["match_id", "date"]], on="match_id", how="left")
    return stats


def _compute_player_bowl_stats(matches_df: pd.DataFrame, balls_df: pd.DataFrame) -> pd.DataFrame:
    balls_12 = balls_df[balls_df["innings"].isin([1, 2])].copy()
    balls_12 = balls_12.merge(matches_df[["match_id", "team1", "team2"]], on="match_id", how="left")

    mask = balls_12["batting_team"] == balls_12["team2"]
    balls_12["bowler_team"] = balls_12["team1"]
    balls_12.loc[mask, "bowler_team"] = balls_12.loc[mask, "team2"]

    balls_12["is_bowler_wicket"] = balls_12["is_wicket"] & ~balls_12["wicket_kind"].isin(
        NON_BOWLER_WICKET_KINDS
    )

    stats = (
        balls_12.groupby(["match_id", "bowler_team", "bowler"])
        .agg(
            runs_conceded=("runs_total", "sum"),
            balls_bowled=("runs_total", "count"),
            wickets=("is_bowler_wicket", "sum"),
            dots=("runs_total", lambda x: int((x == 0).sum())),
        )
        .reset_index()
    )
    stats = stats.rename(columns={"bowler_team": "team"})
    stats = stats.merge(matches_df[["match_id", "date"]], on="match_id", how="left")
    return stats


# ---------------------------------------------------------------------------
# Feature families
# ---------------------------------------------------------------------------


def team_form_features(
    team: str,
    cutoff_date: pd.Timestamp,
    matches_df: pd.DataFrame,
    balls_df: pd.DataFrame,
    team_stats: pd.DataFrame | None = None,
    n: int = 10,
) -> dict:
    if team_stats is None:
        team_stats = _compute_team_stats(matches_df, balls_df)

    hist = team_stats[(team_stats["team"] == team) & (team_stats["date"] < cutoff_date)]

    if hist.empty:
        return {
            "form_matches_played": 0,
            "form_win_rate": 0.0,
            "form_avg_runs_scored": 0.0,
            "form_avg_runs_conceded": 0.0,
            "form_avg_run_rate": 0.0,
            "form_avg_economy": 0.0,
            "form_avg_sixes_hit": 0.0,
            "form_avg_sixes_conceded": 0.0,
            "form_days_since_last_match": 999,
        }

    last_n = hist.sort_values("date").tail(n)
    played = len(last_n)

    total_balls_faced = int(last_n["balls_faced"].sum())
    total_balls_bowled = int(last_n["balls_bowled"].sum())

    win_rate = last_n["won"].mean() if played > 0 else 0.0
    avg_runs_scored = last_n["runs_scored"].mean() if played > 0 else 0.0
    avg_runs_conceded = last_n["runs_conceded"].mean() if played > 0 else 0.0
    avg_run_rate = (
        last_n["runs_scored"].sum() / (total_balls_faced / 6.0) if total_balls_faced > 0 else 0.0
    )
    avg_economy = (
        last_n["runs_conceded"].sum() / (total_balls_bowled / 6.0)
        if total_balls_bowled > 0
        else 0.0
    )
    avg_sixes_hit = last_n["sixes_hit"].mean() if played > 0 else 0.0
    avg_sixes_conceded = last_n["sixes_conceded"].mean() if played > 0 else 0.0
    days_since = int((cutoff_date - last_n["date"].max()).days)

    return {
        "form_matches_played": played,
        "form_win_rate": win_rate,
        "form_avg_runs_scored": avg_runs_scored,
        "form_avg_runs_conceded": avg_runs_conceded,
        "form_avg_run_rate": avg_run_rate,
        "form_avg_economy": avg_economy,
        "form_avg_sixes_hit": avg_sixes_hit,
        "form_avg_sixes_conceded": avg_sixes_conceded,
        "form_days_since_last_match": days_since,
    }


def team_home_away_features(
    team: str,
    cutoff_date: pd.Timestamp,
    matches_df: pd.DataFrame,
    balls_df: pd.DataFrame,
    team_stats: pd.DataFrame | None = None,
    n: int = 10,
) -> dict:
    """Return home/away form features for a single team."""
    if team_stats is None:
        team_stats = _compute_team_stats(matches_df, balls_df)

    hist = team_stats[(team_stats["team"] == team) & (team_stats["date"] < cutoff_date)].copy()

    if hist.empty:
        return {
            "home_matches_played": 0,
            "home_win_rate": 0.0,
            "home_avg_runs_scored": 0.0,
            "away_matches_played": 0,
            "away_win_rate": 0.0,
            "away_avg_runs_scored": 0.0,
        }

    # Classify each match as home or away for this team
    hist["is_home"] = hist["venue"].apply(lambda v: team in get_home_team(v))

    home_hist = hist[hist["is_home"]].sort_values("date").tail(n)
    away_hist = hist[~hist["is_home"]].sort_values("date").tail(n)

    home_played = len(home_hist)
    away_played = len(away_hist)

    home_win_rate = home_hist["won"].mean() if home_played > 0 else 0.0
    home_avg_runs = home_hist["runs_scored"].mean() if home_played > 0 else 0.0

    away_win_rate = away_hist["won"].mean() if away_played > 0 else 0.0
    away_avg_runs = away_hist["runs_scored"].mean() if away_played > 0 else 0.0

    return {
        "home_matches_played": home_played,
        "home_win_rate": home_win_rate,
        "home_avg_runs_scored": home_avg_runs,
        "away_matches_played": away_played,
        "away_win_rate": away_win_rate,
        "away_avg_runs_scored": away_avg_runs,
    }


def player_batting_features(
    team: str,
    cutoff_date: pd.Timestamp,
    matches_df: pd.DataFrame,
    balls_df: pd.DataFrame,
    player_bat_stats: pd.DataFrame | None = None,
    top_k: int = 5,
    n: int = 10,
) -> dict:
    if player_bat_stats is None:
        player_bat_stats = _compute_player_bat_stats(matches_df, balls_df)

    # Team's last 3 matches before cutoff
    team_hist = player_bat_stats[
        (player_bat_stats["team"] == team) & (player_bat_stats["date"] < cutoff_date)
    ][["match_id", "date"]].drop_duplicates()
    last_3 = team_hist.sort_values("date").tail(3)["match_id"].tolist()

    top_batters = []
    if last_3:
        active = (
            player_bat_stats[
                (player_bat_stats["team"] == team)
                & (player_bat_stats["match_id"].isin(last_3))
            ]
            .groupby("batter")["balls"]
            .sum()
            .sort_values(ascending=False)
            .head(top_k)
        )
        top_batters = active.index.tolist()

    out = {}
    for i in range(1, top_k + 1):
        prefix = f"p{i}_bat"
        if i <= len(top_batters):
            batter = top_batters[i - 1]
            hist = (
                player_bat_stats[
                    (player_bat_stats["team"] == team)
                    & (player_bat_stats["batter"] == batter)
                    & (player_bat_stats["date"] < cutoff_date)
                ]
                .sort_values("date")
                .tail(n)
            )
            total_runs = int(hist["runs"].sum())
            total_balls = int(hist["balls"].sum())
            total_sixes = int(hist["sixes"].sum())
            n_inns = len(hist)

            avg_runs = total_runs / n_inns if n_inns > 0 else 0.0
            sr = 100.0 * total_runs / total_balls if total_balls > 0 else 0.0
            sixes_per_inn = total_sixes / n_inns if n_inns > 0 else 0.0
        else:
            avg_runs = 0.0
            sr = 0.0
            sixes_per_inn = 0.0

        out[f"{prefix}_avg_runs"] = avg_runs
        out[f"{prefix}_sr"] = sr
        out[f"{prefix}_sixes_per_inn"] = sixes_per_inn

    return out


def player_bowling_features(
    team: str,
    cutoff_date: pd.Timestamp,
    matches_df: pd.DataFrame,
    balls_df: pd.DataFrame,
    player_bowl_stats: pd.DataFrame | None = None,
    top_k: int = 3,
    n: int = 10,
) -> dict:
    if player_bowl_stats is None:
        player_bowl_stats = _compute_player_bowl_stats(matches_df, balls_df)

    # Team's last 3 matches before cutoff
    team_hist = player_bowl_stats[
        (player_bowl_stats["team"] == team) & (player_bowl_stats["date"] < cutoff_date)
    ][["match_id", "date"]].drop_duplicates()
    last_3 = team_hist.sort_values("date").tail(3)["match_id"].tolist()

    top_bowlers = []
    if last_3:
        active = (
            player_bowl_stats[
                (player_bowl_stats["team"] == team)
                & (player_bowl_stats["match_id"].isin(last_3))
            ]
            .groupby("bowler")["balls_bowled"]
            .sum()
            .sort_values(ascending=False)
            .head(top_k)
        )
        top_bowlers = active.index.tolist()

    out = {}
    for i in range(1, top_k + 1):
        prefix = f"p{i}_bowl"
        if i <= len(top_bowlers):
            bowler = top_bowlers[i - 1]
            hist = (
                player_bowl_stats[
                    (player_bowl_stats["team"] == team)
                    & (player_bowl_stats["bowler"] == bowler)
                    & (player_bowl_stats["date"] < cutoff_date)
                ]
                .sort_values("date")
                .tail(n)
            )
            total_runs = int(hist["runs_conceded"].sum())
            total_balls = int(hist["balls_bowled"].sum())
            total_wkts = int(hist["wickets"].sum())
            total_dots = int(hist["dots"].sum())
            n_inns = len(hist)

            economy = total_runs / (total_balls / 6.0) if total_balls > 0 else 0.0
            wkts_per_inn = total_wkts / n_inns if n_inns > 0 else 0.0
            dot_pct = 100.0 * total_dots / total_balls if total_balls > 0 else 0.0
        else:
            economy = 0.0
            wkts_per_inn = 0.0
            dot_pct = 0.0

        out[f"{prefix}_economy"] = economy
        out[f"{prefix}_wickets_per_inn"] = wkts_per_inn
        out[f"{prefix}_dot_pct"] = dot_pct

    return out


def matchup_features(
    team1: str,
    team2: str,
    venue: str,
    cutoff_date: pd.Timestamp,
    matches_df: pd.DataFrame,
    balls_df: pd.DataFrame,
    team_stats: pd.DataFrame | None = None,
) -> dict:
    hist = matches_df[matches_df["date"] < cutoff_date]

    # Head-to-head
    h2h = hist[
        (
            ((hist["team1"] == team1) & (hist["team2"] == team2))
            | ((hist["team1"] == team2) & (hist["team2"] == team1))
        )
    ].sort_values("date")

    h2h_total = len(h2h)
    h2h_last5 = h2h.tail(5)
    h2h_last5_n = len(h2h_last5)
    h2h_t1_wins = int((h2h_last5["winner"] == team1).sum()) if h2h_last5_n > 0 else 0
    h2h_t2_wins = int((h2h_last5["winner"] == team2).sum()) if h2h_last5_n > 0 else 0
    h2h_t1_win_rate = h2h_t1_wins / h2h_last5_n if h2h_last5_n > 0 else 0.0
    h2h_t2_win_rate = h2h_t2_wins / h2h_last5_n if h2h_last5_n > 0 else 0.0

    # Venue records
    venue_matches = hist[hist["venue"] == venue]

    t1_venue = venue_matches[
        (venue_matches["team1"] == team1) | (venue_matches["team2"] == team1)
    ]
    t1_venue_n = len(t1_venue)
    t1_venue_wins = int((t1_venue["winner"] == team1).sum()) if t1_venue_n > 0 else 0
    t1_venue_win_rate = t1_venue_wins / t1_venue_n if t1_venue_n > 0 else 0.0

    t2_venue = venue_matches[
        (venue_matches["team1"] == team2) | (venue_matches["team2"] == team2)
    ]
    t2_venue_n = len(t2_venue)
    t2_venue_wins = int((t2_venue["winner"] == team2).sum()) if t2_venue_n > 0 else 0
    t2_venue_win_rate = t2_venue_wins / t2_venue_n if t2_venue_n > 0 else 0.0

    # Venue aggregates
    venue_match_ids = venue_matches["match_id"].tolist()
    if venue_match_ids:
        venue_balls = balls_df[
            (balls_df["match_id"].isin(venue_match_ids)) & (balls_df["innings"].isin([1, 2]))
        ]

        first_inns = venue_balls[venue_balls["innings"] == 1]
        first_inns_scores = first_inns.groupby("match_id")["runs_total"].sum()
        venue_avg_first_innings_score = (
            float(first_inns_scores.mean()) if len(first_inns_scores) > 0 else 0.0
        )

        sixes_per_match = venue_balls.groupby("match_id").apply(
            lambda x: int((x["runs_batter"] == 6).sum())
        )
        venue_avg_total_sixes = (
            float(sixes_per_match.mean()) if len(sixes_per_match) > 0 else 0.0
        )
    else:
        venue_avg_first_innings_score = 0.0
        venue_avg_total_sixes = 0.0

    return {
        "h2h_matches_played": h2h_total,
        "h2h_t1_win_rate": h2h_t1_win_rate,
        "h2h_t2_win_rate": h2h_t2_win_rate,
        "t1_venue_matches": t1_venue_n,
        "t1_venue_win_rate": t1_venue_win_rate,
        "t2_venue_matches": t2_venue_n,
        "t2_venue_win_rate": t2_venue_win_rate,
        "venue_avg_first_innings_score": venue_avg_first_innings_score,
        "venue_avg_total_sixes": venue_avg_total_sixes,
    }


def context_features(match_row: pd.Series, matches_df: pd.DataFrame) -> dict:
    season = match_row["season"]
    cutoff_date = match_row["date"]

    season_hist = matches_df[
        (matches_df["season"] == season) & (matches_df["date"] < cutoff_date)
    ].sort_values("date")

    season_match_number = len(season_hist) + 1
    days_into_season = (
        int((cutoff_date - season_hist["date"].min()).days) if not season_hist.empty else 0
    )
    day_of_week = cutoff_date.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0

    return {
        "season_match_number": season_match_number,
        "days_into_season": days_into_season,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
    }


# ---------------------------------------------------------------------------
# Top-level builder
# ---------------------------------------------------------------------------


def build_feature_row(
    match_row: pd.Series,
    matches_df: pd.DataFrame,
    balls_df: pd.DataFrame,
    team_stats: pd.DataFrame | None = None,
    player_bat_stats: pd.DataFrame | None = None,
    player_bowl_stats: pd.DataFrame | None = None,
) -> dict:
    team1 = match_row["team1"]
    team2 = match_row["team2"]
    venue = match_row["venue"]
    cutoff_date = match_row["date"]

    features: dict = {}

    # Match-level home/away context
    home_teams = get_home_team(venue)
    features["is_home_game_t1"] = 1 if team1 in home_teams else 0
    features["is_home_game_t2"] = 1 if team2 in home_teams else 0
    features["is_neutral_venue"] = 1 if not home_teams else 0
    features["is_derby"] = 1 if (team1 in home_teams and team2 in home_teams) else 0

    # Team 1
    t1_form = team_form_features(team1, cutoff_date, matches_df, balls_df, team_stats=team_stats)
    t1_bat = player_batting_features(
        team1, cutoff_date, matches_df, balls_df, player_bat_stats=player_bat_stats
    )
    t1_bowl = player_bowling_features(
        team1, cutoff_date, matches_df, balls_df, player_bowl_stats=player_bowl_stats
    )
    t1_ha = team_home_away_features(team1, cutoff_date, matches_df, balls_df, team_stats=team_stats)
    for d, prefix in ((t1_form, "t1_"), (t1_bat, "t1_"), (t1_bowl, "t1_"), (t1_ha, "t1_")):
        for k, v in d.items():
            features[prefix + k] = v

    # Team 2
    t2_form = team_form_features(team2, cutoff_date, matches_df, balls_df, team_stats=team_stats)
    t2_bat = player_batting_features(
        team2, cutoff_date, matches_df, balls_df, player_bat_stats=player_bat_stats
    )
    t2_bowl = player_bowling_features(
        team2, cutoff_date, matches_df, balls_df, player_bowl_stats=player_bowl_stats
    )
    t2_ha = team_home_away_features(team2, cutoff_date, matches_df, balls_df, team_stats=team_stats)
    for d, prefix in ((t2_form, "t2_"), (t2_bat, "t2_"), (t2_bowl, "t2_"), (t2_ha, "t2_")):
        for k, v in d.items():
            features[prefix + k] = v

    # Matchup & context
    matchup = matchup_features(team1, team2, venue, cutoff_date, matches_df, balls_df, team_stats=team_stats)
    features.update(matchup)
    features.update(context_features(match_row, matches_df))

    # ---- Fix C: high-variance differential features ----
    # 1. Relative form win rate
    features["t1_vs_t2_form_win_rate_diff"] = (
        features.get("t1_form_win_rate", 0.0) - features.get("t2_form_win_rate", 0.0)
    )

    # 2. Venue scoring vs global average
    balls_12 = balls_df[balls_df["innings"].isin([1, 2])]
    hist_matches = matches_df[matches_df["date"] < cutoff_date]
    hist_balls = balls_12[balls_12["match_id"].isin(hist_matches["match_id"])]
    inn1_totals = hist_balls[hist_balls["innings"] == 1].groupby("match_id")["runs_total"].sum()
    global_avg_first = float(inn1_totals.mean()) if len(inn1_totals) > 0 else 0.0
    features["venue_scoring_vs_global_avg"] = (
        matchup.get("venue_avg_first_innings_score", 0.0) - global_avg_first
    )

    # 3. Matchup pace indicator
    features["matchup_pace_indicator"] = (
        features.get("t1_form_avg_run_rate", 0.0) + features.get("t2_form_avg_run_rate", 0.0)
    ) / 2.0

    features["match_id"] = match_row["match_id"]
    return features
