"""Tests for auth endpoints."""


def test_register(client):
    resp = client.post("/auth/register", json={
        "email": "newuser@test.com", "password": "securepass", "name": "New User"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate(client):
    client.post("/auth/register", json={
        "email": "dup@test.com", "password": "pass123", "name": "Dup"
    })
    resp = client.post("/auth/register", json={
        "email": "dup@test.com", "password": "pass123", "name": "Dup"
    })
    assert resp.status_code == 400


def test_login(client):
    client.post("/auth/register", json={
        "email": "login@test.com", "password": "pass123", "name": "Login"
    })
    resp = client.post("/auth/login", json={
        "email": "login@test.com", "password": "pass123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    resp = client.post("/auth/login", json={
        "email": "login@test.com", "password": "wrong"
    })
    assert resp.status_code == 401


def test_me(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@fitgenix.com"


def test_refresh_token(client):
    reg = client.post("/auth/register", json={
        "email": "refresh@test.com", "password": "pass123", "name": "Refresh"
    })
    refresh = reg.json()["refresh_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
