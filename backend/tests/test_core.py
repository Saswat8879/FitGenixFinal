"""Tests for onboarding, profile, plans, and dashboard."""


def test_onboarding(client, auth_headers):
    resp = client.post("/onboarding/survey", headers=auth_headers, json={
        "age": 30, "sex": "male", "height_cm": 175, "weight_kg": 80,
        "goal": "lose_weight", "diet_type": "vegetarian",
        "equipment": ["Dumbbell"], "time_available_min": 30,
        "coaching_style": "moderate", "country": "India",
        "cuisine_preference": "Indian", "activity_level": "sedentary",
        "work_style": "desk_job",
        "type_2_diabetes": False, "pre_diabetes": False,
        "hypertension": True, "high_cholesterol": False,
        "fatty_liver": False, "obesity": False,
        "asthma_copd": False, "back_pain": False,
        "knee_pain": False, "shoulder_pain": False,
        "family_history_diabetes": True,
        "on_medication": False, "doctor_supervised": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "cluster_archetype" in data
    assert data["workout_id"] is not None


def test_get_profile(client, auth_headers):
    resp = client.get("/profile/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["age"] == 30


def test_update_personal(client, auth_headers):
    resp = client.patch("/profile/personal", headers=auth_headers, json={"age": 31})
    assert resp.status_code == 200


def test_dashboard(client, auth_headers):
    resp = client.get("/dashboard/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "user_name" in data


def test_get_today_workout(client, auth_headers):
    resp = client.get("/plans/workout/today", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "exercises" in data


def test_get_today_diet(client, auth_headers):
    resp = client.get("/plans/diet/today", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "meals" in data


def test_regenerate_plans(client, auth_headers):
    resp = client.post("/plans/regenerate", headers=auth_headers,
                       json={"workout": True, "diet": True})
    assert resp.status_code == 200
