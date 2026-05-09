# IPL Event Predictor — Model Card

**Version:** 1.0  
**Date:** 2026-04-22  
**Author:** Generated as part of an end-to-end ML portfolio project.

---

## 1. Dataset Description

The model is trained on **1,193 IPL T20 matches** (2008–2026) parsed from CricSheet JSON files. Each match contains:

- **Match-level metadata:** teams, venue, date, season, toss winner/decision, winner, win margin, player of match
- **Ball-by-ball data:** ~283,000 delivery records spanning innings 1 and 2 (super-over innings excluded from ball-level statistics)

All historical data is treated as **pre-match information only** — features are computed with a strict `cutoff_date < match_date` filter to prevent leakage.

---

## 2. Train / Validation / Test Split

| Split | Seasons | Matches |
|-------|---------|---------|
| Train | 2007/08 – 2021 | 876 |
| Validation | 2022 – 2023 | 148 |
| Test | 2024 – 2026 | 169 |

Splits are **time-aware** (no random shuffling). The validation set is used for hyper-parameter selection; the test set is used for final evaluation only.

---

## 3. Events Covered

29 binary events are modelled, grouped into 8 categories:

| Category | Events |
|----------|--------|
| outcome | match result, toss winner wins, runs ≥300/350/400, super over |
| boundaries | sixes ≥10/15/20, fours ≥20/30/40 |
| individual_batting | any fifty, any century, any big six hitter (≥5 sixes) |
| individual_bowling | any 3-wicket haul, any 4-wicket haul |
| dismissals | any run out, any LBW |
| team_score | team score ≥160/180/200, all out |
| powerplay | PP score ≥50/60, loses PP wicket |
| toss | toss winner wins match |

*Team-scope events* (e.g., `team_wins_match`) produce two labels per match (one per team). *Match-scope events* produce one label per match.

---

## 4. Metrics Summary

| Metric | Value |
|--------|-------|
| Models trained | 27 / 29 |
| Flat base-rate predictors | 2 / 29 (insufficient data) |
| Beating baseline on test | 18 / 29 |
| Best improver | `match_sixes_gte_15` (+24.6% log-loss improvement) |
| Mean test log-loss (trained only) | 0.602 |

Calibration is enforced via `CalibratedClassifierCV` (isotonic, 3-fold) wrapped around XGBoost.

### Full Portfolio Table

| event_id | test_logloss | test_brier | baseline_LL | improvement | status |
|----------|-------------|-----------|-------------|-------------|--------|
| match_sixes_gte_15 | 0.753 | 0.202 | 0.999 | **+24.6%** | trained |
| match_sixes_gte_20 | 0.934 | 0.267 | 1.066 | **+12.4%** | trained |
| team_score_gte_200 | 0.886 | 0.151 | 0.978 | **+9.4%** | trained |
| match_runs_gte_350 | 0.904 | 0.218 | 0.995 | **+9.1%** | trained |
| match_runs_gte_400 | 0.928 | 0.089 | 1.015 | **+8.5%** | trained |
| match_sixes_gte_10 | 0.519 | 0.152 | 0.598 | **+13.1%** | trained |
| team_score_gte_180 | 0.918 | 0.173 | 0.956 | **+3.9%** | trained |
| team_pp_score_gte_50 | 0.827 | 0.146 | 0.847 | **+2.4%** | trained |
| any_run_out | 0.734 | 0.178 | 0.750 | **+2.2%** | trained |
| team_score_gte_160 | 0.717 | 0.176 | 0.731 | **+1.9%** | trained |
| any_big_six_hitter | 0.824 | 0.186 | 0.835 | **+1.3%** | trained |
| team_pp_score_gte_60 | 0.931 | 0.130 | 0.942 | **+1.1%** | trained |
| any_lbw | 0.684 | 0.191 | 0.694 | **+1.4%** | trained |
| any_century | 0.374 | 0.025 | 0.383 | **+2.3%** | trained |
| match_fours_gte_30 | 0.802 | 0.165 | 0.808 | **+0.7%** | trained |
| any_three_wicket_haul | 0.637 | 0.200 | 0.643 | **+0.9%** | trained |
| toss_winner_wins_match | 0.686 | 0.222 | 0.691 | **+0.7%** | trained |
| team_has_top_wicket_taker | 0.650 | 0.198 | 0.650 | **+0.0%** | trained |
| match_goes_super_over | 0.041 | 0.002 | 0.041 | 0.0% | INSUFFICIENT DATA |
| match_fours_gte_40 | 0.442 | 0.062 | 0.442 | 0.0% | INSUFFICIENT DATA |
| team_bats_first | 0.693 | 0.250 | 0.693 | **−0.0%** | trained |
| match_runs_gte_300 | 0.560 | 0.235 | 0.560 | **−0.1%** | trained |
| team_loses_pp_wicket | 0.496 | 0.222 | 0.494 | **−0.4%** | trained |
| team_all_out | 0.380 | 0.073 | 0.377 | **−0.8%** | trained |
| team_wins_match | 0.697 | 0.250 | 0.693 | **−0.5%** | trained |
| team_has_top_scorer | 0.700 | 0.250 | 0.693 | **−1.0%** | trained |
| match_fours_gte_20 | 0.257 | 0.187 | 0.249 | **−3.2%** | trained |
| any_fifty | 0.351 | 0.142 | 0.342 | **−2.6%** | trained |
| any_four_wicket_haul | 0.541 | 0.173 | 0.531 | **−2.1%** | trained |

---

## 5. Known Limitations

### 5.1 Insufficient-data events (flat predictors)

| Event | Issue |
|-------|-------|
| `match_goes_super_over` | Only 1.6% of matches go to a super over. The train set contains **0 positive examples**, so the model falls back to a flat base-rate predictor (always predicts ~1.6%). |
| `match_fours_gte_40` | Only 3.3% of matches have ≥40 fours. The train set has **<30 positives**, triggering the same flat predictor. |

### 5.2 Events that fail to beat baseline (hypotheses)

| Event | Hypothesis |
|-------|-----------|
| `match_fours_gte_20` | Base rate is 86.1% — the event is already almost certain. There is very little signal left to extract; the model slightly overfits to noise. |
| `any_fifty` | Base rate 82.7%. Similarly high base rate. The model may be capturing minor variance but not enough to beat the strong prior. |
| `any_four_wicket_haul` | Base rate 17.5%. This is a rare individual-bowling feat. Player-level bowling features (top-3 bowlers by recent activity) may not capture the true wicket-taking threat of a given lineup. |
| `team_has_top_scorer` | Base rate ~50.7%. This is essentially a coin-flip conditioned on team strength, and both teams' batting features are symmetric, making it hard to separate. |
| `team_wins_match` | Base rate exactly 50%. With no home-ground advantage encoded and roughly symmetric team features, the model cannot reliably out-predict the coin-flip baseline. |
| `team_bats_first` | Base rate 50%. The toss winner chooses to bat or bowl based on conditions; our features do not include pitch report or weather, so prediction is near-random. |
| `team_all_out` | Base rate 8.4%. Very imbalanced. The model may under-predict rare all-out collapses because training optimises log-loss, which is conservative on rare positives. |
| `team_loses_pp_wicket` | Base rate 78.1%. High base rate + the feature set does not explicitly encode early-swing or powerplay-specialist bowler presence. |
| `match_runs_gte_300` | Base rate 60.4%. The threshold is low for T20; most matches cross 300. The model adds no value over the prior. |

---

## 6. Intended Use

**This is a portfolio project, not a production betting tool.**

- The model demonstrates end-to-end ML engineering: data parsing, feature engineering, leakage prevention, calibration, hyper-parameter tuning, and ranking.
- **Do not use for real wagering.** Betting markets include a 5–15% vigorish (bookmaker margin) that this model does not account for. Even a model that beats a constant baseline is unlikely to overcome market inefficiencies after fees.
- Predictions are most useful as **entertainment / narrative generation**: "Given these two teams at this venue, the model thinks a high-sixes game is unusually likely."

---

## 7. What I Would Build Differently

If I were iterating beyond this first pass, three changes would give the biggest returns:

1. **Granular player embeddings.** Currently, player features are hand-rolled aggregates (average runs, strike rate, economy). A learned embedding from a large historical corpus — or even just PCA on player career stats — would capture form, matchup history, and role far better than top-k averages.

2. **Weather and pitch conditions.** The current feature set has no notion of dew, overcast skies, or pitch deterioration. In IPL, these are first-order drivers of total runs and wicket counts. Scraping match-day weather or using venue-specific pitch ratings would lift the `team_bats_first`, `match_runs_gte_*`, and `team_all_out` models specifically.

3. **Temporal dynamics with a rolling window.** All features use a fixed 10-match lookback. A team on a 5-match winning streak should have different momentum weights than a team that won 5 of 10 with alternating results. An exponentially-weighted moving average (EWMA) or a small RNN on the match sequence would capture this.
