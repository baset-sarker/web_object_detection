import pytest
import json
from app import app, init_db
import tempfile
import os


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr("app.DB_PATH", db_file)
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- Health ---

def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "object-detection-api"


# --- POST /api/detections ---

def test_log_detection_success(client):
    res = client.post(
        "/api/detections",
        data=json.dumps({"label": "person", "confidence": 0.92}),
        content_type="application/json",
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["label"] == "person"
    assert data["confidence"] == 0.92
    assert "timestamp" in data


def test_log_detection_missing_label(client):
    res = client.post(
        "/api/detections",
        data=json.dumps({"confidence": 0.5}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_log_detection_missing_confidence(client):
    res = client.post(
        "/api/detections",
        data=json.dumps({"label": "car"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_log_detection_empty_body(client):
    res = client.post("/api/detections", content_type="application/json")
    assert res.status_code == 400


# --- GET /api/detections ---

def test_get_detections_empty(client):
    res = client.get("/api/detections")
    assert res.status_code == 200
    assert res.get_json() == []


def test_get_detections_returns_logged(client):
    client.post(
        "/api/detections",
        data=json.dumps({"label": "dog", "confidence": 0.8}),
        content_type="application/json",
    )
    res = client.get("/api/detections")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["label"] == "dog"
    assert data[0]["confidence"] == 0.8


def test_get_detections_limit_50(client):
    for i in range(55):
        client.post(
            "/api/detections",
            data=json.dumps({"label": f"obj{i}", "confidence": 0.5}),
            content_type="application/json",
        )
    res = client.get("/api/detections")
    assert len(res.get_json()) == 50


def test_get_detections_ordered_newest_first(client):
    for label in ["a", "b", "c"]:
        client.post(
            "/api/detections",
            data=json.dumps({"label": label, "confidence": 0.5}),
            content_type="application/json",
        )
    data = client.get("/api/detections").get_json()
    assert data[0]["label"] == "c"


# --- GET /api/stats ---

def test_stats_empty(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    assert res.get_json() == []


def test_stats_counts_and_avg(client):
    for _ in range(3):
        client.post(
            "/api/detections",
            data=json.dumps({"label": "car", "confidence": 0.9}),
            content_type="application/json",
        )
    client.post(
        "/api/detections",
        data=json.dumps({"label": "person", "confidence": 0.7}),
        content_type="application/json",
    )
    data = client.get("/api/stats").get_json()
    car = next(d for d in data if d["label"] == "car")
    assert car["count"] == 3
    assert car["avg_confidence"] == pytest.approx(0.9, abs=0.001)
    person = next(d for d in data if d["label"] == "person")
    assert person["count"] == 1
