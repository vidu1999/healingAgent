"""GitHub webhook HMAC signature + replay protection tests."""

import json

from app.services.github_adapter import verify_webhook_signature, is_replay


def test_verify_webhook_signature_valid():
    secret = "s3cr3t"
    body = b'{"ref":"refs/heads/main"}'
    import hmac, hashlib
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, sig, secret) is True


def test_verify_webhook_signature_invalid():
    assert verify_webhook_signature(b"body", "sha256=deadbeef", "secret") is False
    assert verify_webhook_signature(b"body", None, "secret") is False
    assert verify_webhook_signature(b"body", "sha256=abc", "") is False


def test_replay_protection():
    seen = {}
    d = "del-1"
    assert is_replay(d, seen) is False
    assert is_replay(d, seen) is True  # replay detected


def test_webhook_endpoint_rejects_bad_signature(client, seed):
    client.post("/api/v1/auth/login", json={"email": "admin@test.example.com", "password": "password123"})
    r = client.post(
        "/api/v1/webhooks/github",
        content=b"{}",
        headers={"x-hub-signature-256": "sha256=bad", "x-github-delivery": "d1", "x-github-event": "push"},
    )
    assert r.status_code in (401, 503), (r.status_code, r.text)
