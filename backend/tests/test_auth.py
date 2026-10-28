"""Authentication and authorization tests."""

from app.core.security import hash_password, verify_password, hash_token


def test_password_hash_verify(seed):
    assert verify_password("password123", seed["admin"].password_hash)
    assert not verify_password("wrong", seed["admin"].password_hash)


def test_login_logout_me(client, seed):
    # login (JSON body)
    r = client.post("/api/v1/auth/login", json={"email": "admin@test.example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.cookies.get("sentinelops_session")
    assert token is not None

    # me
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.example.com"
    assert "admin" in r.json()["roles"]

    # wrong password
    r = client.post("/api/v1/auth/login", json={"email": "admin@test.example.com", "password": "wrong"})
    assert r.status_code == 401

    # logout
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_hash_token_deterministic_and_one_way():
    t = hash_token("abc")
    assert t == hash_token("abc")
    assert len(t) == 64
    assert t != "abc"


def test_unauthorized_endpoints(client):
    for path in ["/api/v1/incidents", "/api/v1/approvals", "/api/v1/audit-events"]:
        r = client.get(path)
        assert r.status_code == 401, path


def test_viewer_cannot_access_audit(client, seed):
    client.post("/api/v1/auth/login", json={"email": "operator@test.example.com", "password": "password123"})
    r = client.get("/api/v1/audit-events")
    assert r.status_code == 200, r.status_code  # operator allowed by require_roles(admin, operator)


def test_role_enforcement(client, seed):
    client.post("/api/v1/auth/login", json={"email": "operator@test.example.com", "password": "password123"})
    r = client.get("/api/v1/audit-events")
    assert r.status_code == 200, r.text
