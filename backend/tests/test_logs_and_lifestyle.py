"""Tests for logging, lifestyle, progress, and lifestyle points."""


def test_log_water(client, auth_headers):
    resp = client.post("/logs/water", headers=auth_headers,
                       json={"amount_ml": 300, "source": "manual"})
    assert resp.status_code == 200
    assert resp.json()["amount_ml"] == 300


def test_water_today(client, auth_headers):
    resp = client.get("/logs/water/today", headers=auth_headers)
    assert resp.status_code == 200
    assert "total_ml" in resp.json()


def test_meal_custom(client, auth_headers):
    resp = client.post("/logs/meal/custom", headers=auth_headers, json={
        "food_name": "Test Rice", "meal_slot": "lunch", "portion_g": 200,
        "calories": 260, "protein": 5, "carbs": 58, "fat": 0.5,
    })
    assert resp.status_code == 200
    assert resp.json()["food_name"] == "Test Rice"


def test_meals_today(client, auth_headers):
    resp = client.get("/logs/meals/today", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_stress_check(client, auth_headers):
    resp = client.post("/lifestyle/stress-check", headers=auth_headers)
    assert resp.status_code == 200
    assert "stress_level" in resp.json()


def test_lifestyle_checkin(client, auth_headers):
    resp = client.post("/lifestyle/checkin", headers=auth_headers, json={
        "sleep_hours": 7.5, "sleep_quality": 4, "mood": 4,
        "hydration_ml": 2000, "sedentary_minutes": 240,
    })
    assert resp.status_code == 200


def test_lifestyle_tips(client, auth_headers):
    resp = client.get("/lifestyle/tips", headers=auth_headers)
    assert resp.status_code == 200
    assert "tips" in resp.json()


def test_health_metrics(client, auth_headers):
    resp = client.get("/health/metrics", headers=auth_headers)
    assert resp.status_code == 200


def test_diabetes_risk(client, auth_headers):
    resp = client.post("/health/risk/diabetes", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["risk_type"] == "diabetes"


def test_log_weight(client, auth_headers):
    resp = client.post("/progress/weight", headers=auth_headers,
                       json={"weight_kg": 79.5, "notes": "test"})
    assert resp.status_code == 200
    assert resp.json()["bmi"] is not None


def test_goal_progress(client, auth_headers):
    resp = client.get("/progress/goal", headers=auth_headers)
    assert resp.status_code == 200
    assert "percent" in resp.json()


def test_lifestyle_points_today(client, auth_headers):
    resp = client.get("/lifestyle-points/today", headers=auth_headers)
    assert resp.status_code == 200
    assert "total" in resp.json()
    assert "breakdown" in resp.json()


def test_lifestyle_points_history(client, auth_headers):
    resp = client.get("/lifestyle-points/history?days=7", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
