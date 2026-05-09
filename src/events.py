"""Event catalog and per-match label computation for IPL predictor."""

from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Event catalog
# ---------------------------------------------------------------------------

EVENT_CATALOG: list[dict[str, Any]] = [
    # Match-scope events
    {
        "event_id": "match_goes_super_over",
        "display_name": "Match goes to a super over",
        "category": "outcome",
        "scope": "match",
        "description": "Result is tie and winner is not null (super over decided it)",
    },
    {
        "event_id": "toss_winner_wins_match",
        "display_name": "Toss winner wins match",
        "category": "toss",
        "scope": "match",
        "description": "Toss winner equals match winner",
    },
    {
        "event_id": "match_runs_gte_300",
        "display_name": "Match total runs ≥ 300",
        "category": "outcome",
        "scope": "match",
        "description": "Total runs across innings 1+2 ≥ 300",
    },
    {
        "event_id": "match_runs_gte_350",
        "display_name": "Match total runs ≥ 350",
        "category": "outcome",
        "scope": "match",
        "description": "Total runs across innings 1+2 ≥ 350",
    },
    {
        "event_id": "match_runs_gte_400",
        "display_name": "Match total runs ≥ 400",
        "category": "outcome",
        "scope": "match",
        "description": "Total runs across innings 1+2 ≥ 400",
    },
    {
        "event_id": "match_sixes_gte_10",
        "display_name": "Match sixes ≥ 10",
        "category": "boundaries",
        "scope": "match",
        "description": "Count of batter sixes across innings 1+2 ≥ 10",
    },
    {
        "event_id": "match_sixes_gte_15",
        "display_name": "Match sixes ≥ 15",
        "category": "boundaries",
        "scope": "match",
        "description": "Count of batter sixes across innings 1+2 ≥ 15",
    },
    {
        "event_id": "match_sixes_gte_20",
        "display_name": "Match sixes ≥ 20",
        "category": "boundaries",
        "scope": "match",
        "description": "Count of batter sixes across innings 1+2 ≥ 20",
    },
    {
        "event_id": "match_fours_gte_20",
        "display_name": "Match fours ≥ 20",
        "category": "boundaries",
        "scope": "match",
        "description": "Count of batter fours across innings 1+2 ≥ 20",
    },
    {
        "event_id": "match_fours_gte_30",
        "display_name": "Match fours ≥ 30",
        "category": "boundaries",
        "scope": "match",
        "description": "Count of batter fours across innings 1+2 ≥ 30",
    },
    {
        "event_id": "match_fours_gte_40",
        "display_name": "Match fours ≥ 40",
        "category": "boundaries",
        "scope": "match",
        "description": "Count of batter fours across innings 1+2 ≥ 40",
    },
    # Team-scope individual events (converted from match-scope in Fix3)
    {
        "event_id": "any_fifty",
        "display_name": "Team produces a fifty",
        "category": "individual_batting",
        "scope": "team",
        "description": "Any batter from this team scores ≥ 50 runs in their primary innings",
    },
    {
        "event_id": "any_century",
        "display_name": "Team produces a century",
        "category": "individual_batting",
        "scope": "team",
        "description": "Any batter from this team scores ≥ 100 runs in their primary innings",
    },
    {
        "event_id": "any_big_six_hitter",
        "display_name": "Team produces a big six hitter (≥5 sixes)",
        "category": "individual_batting",
        "scope": "team",
        "description": "Any batter from this team hits ≥ 5 sixes in their primary innings",
    },
    {
        "event_id": "any_three_wicket_haul",
        "display_name": "Team produces a three-wicket haul",
        "category": "individual_bowling",
        "scope": "team",
        "description": "Any bowler from this team gets ≥ 3 bowler-credited wickets",
    },
    {
        "event_id": "any_four_wicket_haul",
        "display_name": "Team produces a four-wicket haul",
        "category": "individual_bowling",
        "scope": "team",
        "description": "Any bowler from this team gets ≥ 4 bowler-credited wickets",
    },
    {
        "event_id": "any_run_out",
        "display_name": "Any run out in match",
        "category": "dismissals",
        "scope": "match",
        "description": "At least one run out occurs",
    },
    {
        "event_id": "any_lbw",
        "display_name": "Any LBW in match",
        "category": "dismissals",
        "scope": "match",
        "description": "At least one LBW dismissal occurs",
    },
    # Team-scope events
    {
        "event_id": "team_wins_match",
        "display_name": "Team wins match",
        "category": "outcome",
        "scope": "team",
        "description": "Team equals match winner",
    },
    {
        "event_id": "team_bats_first",
        "display_name": "Team bats first",
        "category": "outcome",
        "scope": "team",
        "description": "Team batted in innings 1",
    },
    {
        "event_id": "team_score_gte_160",
        "display_name": "Team score ≥ 160",
        "category": "team_score",
        "scope": "team",
        "description": "Team's primary innings total ≥ 160",
    },
    {
        "event_id": "team_score_gte_180",
        "display_name": "Team score ≥ 180",
        "category": "team_score",
        "scope": "team",
        "description": "Team's primary innings total ≥ 180",
    },
    {
        "event_id": "team_score_gte_200",
        "display_name": "Team score ≥ 200",
        "category": "team_score",
        "scope": "team",
        "description": "Team's primary innings total ≥ 200",
    },
    {
        "event_id": "team_all_out",
        "display_name": "Team all out",
        "category": "team_score",
        "scope": "team",
        "description": "Team lost 10 wickets in their primary innings",
    },
    {
        "event_id": "team_pp_score_gte_50",
        "display_name": "Team powerplay score ≥ 50",
        "category": "powerplay",
        "scope": "team",
        "description": "Team's score in overs 0-5 of primary innings ≥ 50",
    },
    {
        "event_id": "team_pp_score_gte_60",
        "display_name": "Team powerplay score ≥ 60",
        "category": "powerplay",
        "scope": "team",
        "description": "Team's score in overs 0-5 of primary innings ≥ 60",
    },
    {
        "event_id": "team_loses_pp_wicket",
        "display_name": "Team loses a powerplay wicket",
        "category": "powerplay",
        "scope": "team",
        "description": "Team lost ≥ 1 wicket in overs 0-5 of primary innings",
    },
    {
        "event_id": "team_has_top_scorer",
        "display_name": "Team has top run-scorer",
        "category": "individual_batting",
        "scope": "team",
        "description": "Top run-scorer in match (innings 1+2) belongs to this team",
    },
    {
        "event_id": "team_has_top_wicket_taker",
        "display_name": "Team has top wicket-taker",
        "category": "individual_bowling",
        "scope": "team",
        "description": "Top bowler-credited wicket-taker belongs to this team",
    },
]

# Lookup helpers
MATCH_EVENTS = [e for e in EVENT_CATALOG if e["scope"] == "match"]
TEAM_EVENTS = [e for e in EVENT_CATALOG if e["scope"] == "team"]

# Wicket kinds that do NOT credit the bowler
NON_BOWLER_WICKET_KINDS = {
    "run out",
    "retired hurt",
    "retired out",
    "obstructing the field",
    "timed out",
}


def _is_bowler_wicket(row: pd.Series) -> bool:
    """Return True if the wicket on this ball credits the bowler."""
    if not row["is_wicket"]:
        return False
    return row.get("wicket_kind") not in NON_BOWLER_WICKET_KINDS


# ---------------------------------------------------------------------------
# Match-scope event computers
# ---------------------------------------------------------------------------

def _ev_match_goes_super_over(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int(match_row["result"] == "tie" and pd.notna(match_row["winner"]))


def _ev_toss_winner_wins_match(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int(match_row["toss_winner"] == match_row["winner"])


def _ev_match_runs_gte_300(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int(balls_12["runs_total"].sum() >= 300)


def _ev_match_runs_gte_350(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int(balls_12["runs_total"].sum() >= 350)


def _ev_match_runs_gte_400(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int(balls_12["runs_total"].sum() >= 400)


def _ev_match_sixes_gte_10(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int((balls_12["runs_batter"] == 6).sum() >= 10)


def _ev_match_sixes_gte_15(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int((balls_12["runs_batter"] == 6).sum() >= 15)


def _ev_match_sixes_gte_20(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int((balls_12["runs_batter"] == 6).sum() >= 20)


def _ev_match_fours_gte_20(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int((balls_12["runs_batter"] == 4).sum() >= 20)


def _ev_match_fours_gte_30(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int((balls_12["runs_batter"] == 4).sum() >= 30)


def _ev_match_fours_gte_40(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int((balls_12["runs_batter"] == 4).sum() >= 40)


def _ev_any_fifty(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    if tb.empty:
        return 0
    batter_runs = tb.groupby("batter")["runs_batter"].sum()
    return int((batter_runs >= 50).any())


def _ev_any_century(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    if tb.empty:
        return 0
    batter_runs = tb.groupby("batter")["runs_batter"].sum()
    return int((batter_runs >= 100).any())


def _ev_any_big_six_hitter(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    if tb.empty:
        return 0
    sixes = tb[tb["runs_batter"] == 6]
    if sixes.empty:
        return 0
    six_counts = sixes.groupby(["innings", "batter"]).size()
    return int((six_counts >= 5).any())


def _ev_any_three_wicket_haul(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    if balls_12.empty:
        return 0
    # Bowler is "from team" when they bowl against the opposition
    # Filter to balls where batting_team != team (i.e., team is bowling)
    bowling_balls = balls_12[balls_12["batting_team"] != team]
    if bowling_balls.empty:
        return 0
    mask = bowling_balls.apply(_is_bowler_wicket, axis=1)
    if not mask.any():
        return 0
    wkts = bowling_balls.loc[mask, "bowler"].value_counts()
    return int((wkts >= 3).any())


def _ev_any_four_wicket_haul(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    if balls_12.empty:
        return 0
    bowling_balls = balls_12[balls_12["batting_team"] != team]
    if bowling_balls.empty:
        return 0
    mask = bowling_balls.apply(_is_bowler_wicket, axis=1)
    if not mask.any():
        return 0
    wkts = bowling_balls.loc[mask, "bowler"].value_counts()
    return int((wkts >= 4).any())


def _ev_any_run_out(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int((balls_12["wicket_kind"] == "run out").any())


def _ev_any_lbw(match_row: pd.Series, balls_12: pd.DataFrame) -> int:
    return int((balls_12["wicket_kind"] == "lbw").any())


MATCH_COMPUTERS = {
    "match_goes_super_over": _ev_match_goes_super_over,
    "toss_winner_wins_match": _ev_toss_winner_wins_match,
    "match_runs_gte_300": _ev_match_runs_gte_300,
    "match_runs_gte_350": _ev_match_runs_gte_350,
    "match_runs_gte_400": _ev_match_runs_gte_400,
    "match_sixes_gte_10": _ev_match_sixes_gte_10,
    "match_sixes_gte_15": _ev_match_sixes_gte_15,
    "match_sixes_gte_20": _ev_match_sixes_gte_20,
    "match_fours_gte_20": _ev_match_fours_gte_20,
    "match_fours_gte_30": _ev_match_fours_gte_30,
    "match_fours_gte_40": _ev_match_fours_gte_40,
    "any_run_out": _ev_any_run_out,
    "any_lbw": _ev_any_lbw,
}


# ---------------------------------------------------------------------------
# Team-scope event computers
# ---------------------------------------------------------------------------

def _team_balls(balls_12: pd.DataFrame, team: str) -> pd.DataFrame:
    """Return balls for the team's primary innings (innings 1 or 2)."""
    return balls_12[balls_12["batting_team"] == team]


def _ev_team_wins_match(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    return int(match_row["winner"] == team)


def _ev_team_bats_first(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    team_inns = balls_12[balls_12["batting_team"] == team]["innings"].unique()
    return int(1 in team_inns)


def _ev_team_score_gte_160(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    return int(tb["runs_total"].sum() >= 160) if not tb.empty else 0


def _ev_team_score_gte_180(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    return int(tb["runs_total"].sum() >= 180) if not tb.empty else 0


def _ev_team_score_gte_200(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    return int(tb["runs_total"].sum() >= 200) if not tb.empty else 0


def _ev_team_all_out(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    if tb.empty:
        return 0
    return int(tb["is_wicket"].sum() >= 10)


def _ev_team_pp_score_gte_50(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    pp = tb[tb["over"] <= 5]
    return int(pp["runs_total"].sum() >= 50) if not pp.empty else 0


def _ev_team_pp_score_gte_60(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    pp = tb[tb["over"] <= 5]
    return int(pp["runs_total"].sum() >= 60) if not pp.empty else 0


def _ev_team_loses_pp_wicket(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    tb = _team_balls(balls_12, team)
    pp = tb[tb["over"] <= 5]
    return int(pp["is_wicket"].sum() >= 1) if not pp.empty else 0


def _ev_team_has_top_scorer(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    if balls_12.empty:
        return 0
    batter_runs = balls_12.groupby(["batter", "batting_team"])["runs_batter"].sum().reset_index()
    max_runs = batter_runs["runs_batter"].max()
    top_teams = set(batter_runs[batter_runs["runs_batter"] == max_runs]["batting_team"].unique())
    return int(team in top_teams)


def _ev_team_has_top_wicket_taker(match_row: pd.Series, balls_12: pd.DataFrame, team: str) -> int:
    if balls_12.empty:
        return 0
    mask = balls_12.apply(_is_bowler_wicket, axis=1)
    if not mask.any():
        return 0
    bowlers = balls_12.loc[mask].copy()
    # Determine bowler's team: they are bowling against the batting_team
    # So bowler's team is the other team in the match
    teams = set(balls_12["batting_team"].unique())
    # Map each innings to bowling team
    inns_batting = balls_12.groupby("innings")["batting_team"].first().to_dict()
    inns_bowling = {inn: [t for t in teams if t != bat][0] for inn, bat in inns_batting.items()}
    bowlers["bowler_team"] = bowlers["innings"].map(inns_bowling)
    wkts = bowlers.groupby(["bowler", "bowler_team"]).size().reset_index(name="wickets")
    max_wkts = wkts["wickets"].max()
    top_teams = set(wkts[wkts["wickets"] == max_wkts]["bowler_team"].unique())
    return int(team in top_teams)


TEAM_COMPUTERS = {
    "team_wins_match": _ev_team_wins_match,
    "team_bats_first": _ev_team_bats_first,
    "team_score_gte_160": _ev_team_score_gte_160,
    "team_score_gte_180": _ev_team_score_gte_180,
    "team_score_gte_200": _ev_team_score_gte_200,
    "team_all_out": _ev_team_all_out,
    "team_pp_score_gte_50": _ev_team_pp_score_gte_50,
    "team_pp_score_gte_60": _ev_team_pp_score_gte_60,
    "team_loses_pp_wicket": _ev_team_loses_pp_wicket,
    "team_has_top_scorer": _ev_team_has_top_scorer,
    "team_has_top_wicket_taker": _ev_team_has_top_wicket_taker,
    # Converted from match-scope in Fix3
    "any_fifty": _ev_any_fifty,
    "any_century": _ev_any_century,
    "any_big_six_hitter": _ev_any_big_six_hitter,
    "any_three_wicket_haul": _ev_any_three_wicket_haul,
    "any_four_wicket_haul": _ev_any_four_wicket_haul,
}


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def compute_labels_for_match(match_row: pd.Series, match_balls: pd.DataFrame) -> list[dict[str, Any]]:
    """Return one dict per (event × team-if-applicable) for a single match."""
    outcomes: list[dict[str, Any]] = []

    # No-result => everything is NA, but we still generate rows
    is_no_result = match_row.get("result") == "no result"

    # Filter to regular innings for stats
    balls_12 = match_balls[match_balls["innings"].isin([1, 2])].copy()

    # Match-scope events
    for ev in MATCH_EVENTS:
        eid = ev["event_id"]
        if is_no_result:
            val = pd.NA
        else:
            val = MATCH_COMPUTERS[eid](match_row, balls_12)
        outcomes.append({
            "match_id": match_row["match_id"],
            "event_id": eid,
            "team": pd.NA,
            "outcome": val,
        })

    # Team-scope events
    team1 = match_row["team1"]
    team2 = match_row["team2"]
    for team in (team1, team2):
        for ev in TEAM_EVENTS:
            eid = ev["event_id"]
            if is_no_result:
                val = pd.NA
            else:
                val = TEAM_COMPUTERS[eid](match_row, balls_12, team)
            outcomes.append({
                "match_id": match_row["match_id"],
                "event_id": eid,
                "team": team,
                "outcome": val,
            })

    return outcomes
