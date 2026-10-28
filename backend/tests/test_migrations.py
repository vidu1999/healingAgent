"""Alembic migration tests: upgrade head from clean DB."""

import subprocess
import sys
import os
import tempfile


def test_alembic_upgrade_head():
    tmp_db = os.path.join(tempfile.gettempdir(), "sentinelops_migration_test.db")
    if os.path.exists(tmp_db):
        os.remove(tmp_db)
    env = dict(os.environ)
    env["DATABASE_URL"] = "sqlite:///" + tmp_db
    env["PYTHONPATH"] = "/home/user/healingAgent/backend"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd="/home/user/healingAgent/backend",
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    sys.path.insert(0, "/home/user/healingAgent/backend")
    from sqlalchemy import create_engine, inspect

    eng = create_engine("sqlite:///" + tmp_db)
    names = inspect(eng).get_table_names()
    assert "users" in names
    assert "audit_events" in names
