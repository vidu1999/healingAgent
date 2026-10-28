"""Patch path validation, hashing, secret scanning tests."""

import os, tempfile

from app.services.patch_service import (
    sha256_of,
    validate_diff_paths,
    scan_for_secrets,
    scan_suspicious_unicode,
    build_patch_artifact,
)


def test_diff_hashing_deterministic():
    diff = "diff --git a/foo.py b/foo.py\n+print('hi')\n"
    h1 = sha256_of(diff)
    h2 = sha256_of(diff)
    assert h1 == h2
    assert len(h1) == 64
    assert sha256_of(diff + "x") != h1


def test_validate_diff_paths_rejects_traversal():
    diff = "diff --git a/../../etc/passwd b/../../etc/passwd\n"
    try:
        validate_diff_paths(diff, tempfile.gettempdir())
        raise AssertionError("should reject traversal")
    except ValueError:
        pass


def test_validate_diff_paths_rejects_absolute():
    diff = "diff --git a//etc/passwd b//etc/passwd\n"
    try:
        validate_diff_paths(diff, tempfile.gettempdir())
        raise AssertionError("should reject absolute")
    except ValueError:
        pass


def test_validate_diff_paths_ok(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x")
    diff = "diff --git a/src/a.py b/src/a.py\n+print(1)\n"
    changed = validate_diff_paths(diff, str(tmp_path))
    assert "src/a.py" in changed


def test_scan_for_secrets():
    findings = scan_for_secrets("api_key = sk-live-1234567890\n")
    assert len(findings) >= 1


def test_scan_suspicious_unicode():
    findings = scan_suspicious_unicode("print(\u200b'x')\n")
    assert len(findings) >= 1


def test_build_patch_artifact():
    diff = "diff --git a/a.py b/a.py\n+print(1)\n"
    art = build_patch_artifact(diff, explanation="fixes bug", files_changed=["a.py"])
    assert art["sha256"] == sha256_of(diff)
    assert art["explanation"] == "fixes bug"
    assert art["files_changed"] == ["a.py"]
