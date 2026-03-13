"""Tests for community and chat endpoints."""


def test_leaderboard(client):
    resp = client.get("/community/leaderboard")
    assert resp.status_code == 200
    assert "entries" in resp.json()


def test_my_rank(client, auth_headers):
    resp = client.get("/community/my-rank", headers=auth_headers)
    assert resp.status_code == 200


def test_chat(client, auth_headers):
    resp = client.post("/chat/", headers=auth_headers,
                       json={"message": "What are good exercises for diabetics?"})
    assert resp.status_code == 200
    assert "response" in resp.json()


def test_chat_history(client, auth_headers):
    resp = client.get("/chat/history", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["app"] == "FitGenix"


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
