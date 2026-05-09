"""FastAPI backend for IPL predictor."""

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure src/ is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from predict_v2 import predict_match
from venue_mapping import VENUE_TO_HOME_TEAM
from features import build_feature_row, precompute_all

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
API_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    team1: str
    team2: str
    venue: str
    match_date: str


class PredictResponse(BaseModel):
    meta: dict
    all_predictions: list[dict]
    top_5_likely: list[dict]
    top_5_notable: list[dict]


class HealthResponse(BaseModel):
    status: str
    models_loaded: int


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load_matches() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "matches.parquet")


def _get_active_teams(matches_df: pd.DataFrame) -> list[str]:
    """Return teams that played at least 1 match in 2024 or later."""
    recent = matches_df[matches_df["date"] >= pd.Timestamp("2024-01-01")]
    teams = set(recent["team1"]) | set(recent["team2"])
    # Deduplicate franchise renames: keep latest name
    rename_map = {
        "Kings XI Punjab": "Punjab Kings",
        "Delhi Daredevils": "Delhi Capitals",
        "Deccan Chargers": "Sunrisers Hyderabad",
        "Rising Pune Supergiant": "Rising Pune Supergiants",
        "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    }
    teams = {rename_map.get(t, t) for t in teams}
    # Filter out defunct teams that only exist in rename map values but never played recently
    active = sorted(t for t in teams if t not in rename_map.values() or t in (set(recent["team1"]) | set(recent["team2"])))
    return sorted(set(active))


def _get_venue_list(matches_df: pd.DataFrame) -> list[dict]:
    venue_counts = matches_df["venue"].value_counts().to_dict()
    results = []
    for venue, home_teams in VENUE_TO_HOME_TEAM.items():
        count = venue_counts.get(venue, 0)
        if count > 0:
            results.append({
                "venue": venue,
                "home_teams": sorted(home_teams),
                "is_neutral": not bool(home_teams),
                "matches_in_dataset": int(count),
            })
    return sorted(results, key=lambda x: x["venue"])


def _extract_feature_importances(model, feature_names: list[str]) -> list[dict]:
    """Extract averaged feature importances from a calibrated XGBoost pipeline."""
    try:
        cal = model.named_steps["xgb"]
        imp_sum = np.zeros(len(feature_names))
        for cc in cal.calibrated_classifiers_:
            imp_sum += cc.estimator.feature_importances_
        avg_imp = imp_sum / len(cal.calibrated_classifiers_)
        paired = list(zip(feature_names, avg_imp))
        paired.sort(key=lambda x: x[1], reverse=True)
        return [{"feature": f, "importance": round(float(i), 5)} for f, i in paired[:10]]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Lifespan: load models at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.matches = _load_matches()
    app.state.balls = pd.read_parquet(PROCESSED_DIR / "balls.parquet")
    app.state.catalog = pd.read_parquet(PROCESSED_DIR / "events_catalog.parquet")
    app.state.metrics = pd.read_parquet(PROCESSED_DIR / "metrics.parquet")
    app.state.venues = _get_venue_list(app.state.matches)
    app.state.teams = _get_active_teams(app.state.matches)

    # Precompute feature aggregates once at startup
    app.state.precomputed = precompute_all(app.state.matches, app.state.balls)

    # Load all models
    app.state.models = {}
    for _, ev in app.state.catalog.iterrows():
        event_id = ev["event_id"]
        path = MODELS_DIR / f"{event_id}.joblib"
        if path.exists():
            app.state.models[event_id] = joblib.load(path)

    # Feature names for importance extraction
    features_with_teams = pd.read_parquet(PROCESSED_DIR / "features.parquet").merge(
        app.state.matches[["match_id", "team1", "team2"]], on="match_id", how="left"
    )
    meta_cols = ["match_id", "team1", "team2"]
    app.state.feature_names = [c for c in features_with_teams.columns if c not in meta_cols]

    yield


app = FastAPI(
    title="IPL Predictor API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow local dev and any Railway-deployed frontend
_origins = os.getenv("CORS_ORIGINS", "")
if _origins:
    allow_origins = [o.strip() for o in _origins.split(",") if o.strip()]
else:
    allow_origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return {"status": "ok", "models_loaded": len(app.state.models)}


@app.get("/api/venues")
async def venues():
    return app.state.venues


@app.get("/api/teams")
async def teams():
    return app.state.teams


@app.post("/api/predict")
async def predict(req: PredictRequest):
    try:
        # Validate teams
        if req.team1 not in app.state.teams:
            raise HTTPException(status_code=400, detail=f"Unknown team: '{req.team1}'. See /api/teams for valid values.")
        if req.team2 not in app.state.teams:
            raise HTTPException(status_code=400, detail=f"Unknown team: '{req.team2}'. See /api/teams for valid values.")
        if req.team1 == req.team2:
            raise HTTPException(status_code=400, detail="team1 and team2 must be different.")

        # Validate venue
        venue_names = {v["venue"] for v in app.state.venues}
        if req.venue not in venue_names:
            raise HTTPException(status_code=400, detail=f"Unknown venue: '{req.venue}'. See /api/venues for valid values.")

        # Validate date
        try:
            pd.Timestamp(req.match_date)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid date format: '{req.match_date}'. Use YYYY-MM-DD.")

        result = predict_match(req.team1, req.team2, req.venue, req.match_date, precomputed=app.state.precomputed, models=app.state.models)

        # Build key features snapshot
        match_row = pd.Series({
            "match_id": f"predict_{req.match_date}_{req.team1[:3]}_v_{req.team2[:3]}",
            "team1": req.team1,
            "team2": req.team2,
            "venue": req.venue,
            "date": pd.Timestamp(req.match_date),
            "season": str(pd.Timestamp(req.match_date).year),
            "city": None,
        })
        features_dict = build_feature_row(match_row, app.state.matches, app.state.balls, **app.state.precomputed)

        from venue_mapping import get_home_team
        home_teams = get_home_team(req.venue)

        meta = {
            "team1": req.team1,
            "team2": req.team2,
            "venue": req.venue,
            "match_date": req.match_date,
            "is_home_game_t1": req.team1 in home_teams,
            "is_home_game_t2": req.team2 in home_teams,
            "is_neutral_venue": not bool(home_teams),
            "key_features": {
                k: round(float(features_dict.get(k, 0)), 3)
                for k in [
                    "t1_form_win_rate",
                    "t2_form_win_rate",
                    "t1_home_win_rate",
                    "venue_avg_first_innings_score",
                    "venue_avg_total_sixes",
                    "h2h_t1_win_rate",
                ]
            },
        }

        all_preds = result["all_probabilities"]
        top_likely = result["variants"]["mmr_0.3"]["top_5_likely"]
        top_notable = result["variants"]["mmr_0.3"]["top_5_notable"]

        return {
            "meta": meta,
            "all_predictions": all_preds,
            "top_5_likely": top_likely,
            "top_5_notable": top_notable,
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Internal prediction error. Please try again.")


@app.get("/api/track-record")
async def track_record():
    path = API_DIR / "data" / "track_record.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Track record data not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/event-importance/{event_id}")
async def event_importance(event_id: str):
    model = app.state.models.get(event_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model not found for event: {event_id}")

    ev_info = app.state.catalog[app.state.catalog["event_id"] == event_id]
    if ev_info.empty:
        raise HTTPException(status_code=404, detail=f"Event not found: {event_id}")

    display_name = ev_info.iloc[0]["display_name"]
    features = _extract_feature_importances(model, app.state.feature_names)

    return {
        "event_id": event_id,
        "display_name": display_name,
        "features": features,
    }


@app.get("/api/model-card")
async def model_card():
    path = PROJECT_ROOT / "MODEL_CARD.md"
    if path.exists():
        content = path.read_text(encoding="utf-8")
    else:
        content = "Model card coming soon."
    return {"content": content}

# ---------------------------------------------------------------------------
# Static files (production frontend build)
# ---------------------------------------------------------------------------

FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # Vite production build outputs assets to /assets/
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/favicon.svg", include_in_schema=False)
    async def favicon():
        return FileResponse(str(FRONTEND_DIST / "favicon.svg"))

    @app.get("/icons.svg", include_in_schema=False)
    async def icons():
        return FileResponse(str(FRONTEND_DIST / "icons.svg"))

    # SPA catch-all: serve index.html for any non-API route so React Router works
    @app.get("/{catchall:path}", include_in_schema=False)
    async def serve_spa(catchall: str):
        if catchall.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        raise HTTPException(status_code=404, detail="Frontend build not found")
else:
    @app.get("/")
    async def root():
        return {"message": "IPL Predictor API is running. Frontend build not found."}
