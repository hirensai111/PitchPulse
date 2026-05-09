"""Basic pytest sanity tests for the IPL Predictor API."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["models_loaded"] == 29


def test_teams(client):
    response = client.get("/api/teams")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    assert "Mumbai Indians" in data
    assert "Chennai Super Kings" in data


def test_venues(client):
    response = client.get("/api/venues")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 50
    venues = {v["venue"] for v in data}
    assert "Wankhede Stadium" in venues


def test_predict_valid(client):
    payload = {
        "team1": "Mumbai Indians",
        "team2": "Chennai Super Kings",
        "venue": "Wankhede Stadium",
        "match_date": "2026-05-01",
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert "all_predictions" in data
    assert "top_5_likely" in data
    assert "top_5_notable" in data
    assert len(data["all_predictions"]) == 45  # 13 match + 16 team x 2
    assert len(data["top_5_likely"]) == 5
    assert len(data["top_5_notable"]) == 5
    assert data["meta"]["is_home_game_t1"] is True
    assert data["meta"]["is_home_game_t2"] is False


def test_predict_unknown_team(client):
    payload = {
        "team1": "Unknown Team",
        "team2": "Chennai Super Kings",
        "venue": "Wankhede Stadium",
        "match_date": "2026-05-01",
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 400
    assert "Unknown team" in response.json()["detail"]


def test_predict_same_team(client):
    payload = {
        "team1": "Mumbai Indians",
        "team2": "Mumbai Indians",
        "venue": "Wankhede Stadium",
        "match_date": "2026-05-01",
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 400


def test_event_importance(client):
    response = client.get("/api/event-importance/match_sixes_gte_15")
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "match_sixes_gte_15"
    assert len(data["features"]) == 10
    assert "feature" in data["features"][0]
    assert "importance" in data["features"][0]


def test_event_importance_not_found(client):
    response = client.get("/api/event-importance/nonexistent_event")
    assert response.status_code == 404


def test_track_record(client):
    response = client.get("/api/track-record")
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert "summary" in data
    assert len(data["matches"]) == 5


def test_model_card(client):
    response = client.get("/api/model-card")
    assert response.status_code == 200
    assert "content" in response.json()
