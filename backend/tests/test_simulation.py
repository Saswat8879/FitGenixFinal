"""Tests for simulation endpoints."""


def test_sim_full_day(client, auth_headers):
    resp = client.post("/simulate/full-day", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulation_type"] == "full_day"
    assert "lifestyle_points" in data["data"]


def test_sim_stress_spike(client, auth_headers):
    resp = client.post("/simulate/stress-spike", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulation_type"] == "stress_spike"


def test_sim_weight_trend(client, auth_headers):
    resp = client.post("/simulate/weight-trend", headers=auth_headers,
                       json={"direction": "loss", "days": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]["entries"]) == 10


def test_sim_meal_log(client, auth_headers):
    resp = client.post("/simulate/meal-log", headers=auth_headers)
    assert resp.status_code == 200


def test_sim_workout_complete(client, auth_headers):
    resp = client.post("/simulate/workout-complete", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "completed"


def test_sim_reset(client, auth_headers):
    resp = client.post("/simulate/reset", headers=auth_headers)
    assert resp.status_code == 200
    assert "deleted" in resp.json()
