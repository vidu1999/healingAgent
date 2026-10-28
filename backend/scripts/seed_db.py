"""Development database seed.

Creates roles (admin, operator, viewer), a default admin user, and system
settings. Intended for local development only. Never run in production without
reviewing; production secrets must come from the environment.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "/home/user/healingAgent/backend")

from app.core.security import hash_password
from app.db.session import engine, session_factory
from app.db.base import Base
import app.models.all  # noqa: F401
from app.models.all import Role, User, UserRole, SystemSetting


def main() -> None:
    Base.metadata.create_all(bind=engine())
    db = session_factory()()
    try:
        roles = [
            Role(name="admin", description="Full access"),
            Role(name="operator", description="Can investigate, repair, approve"),
            Role(name="viewer", description="Read-only dashboard access"),
        ]
        for r in roles:
            if not db.query(Role).filter(Role.name == r.name).first():
                db.add(r)
        db.flush()

        admin = db.query(User).filter(User.email == "admin@sentinelops.dev").first()
        if not admin:
            admin = User(
                email="admin@sentinelops.dev",
                username="admin",
                password_hash=hash_password("admin123"),  # dev only - change in production
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            db.flush()
        for role in db.query(Role).filter(Role.name.in_(["admin", "operator"])).all():
            if not db.query(UserRole).filter(UserRole.user_id == admin.id, UserRole.role_id == role.id).first():
                db.add(UserRole(user_id=admin.id, role_id=role.id))

        settings_seed = {
            "APP_ENV": "development",
            "DEMO_MODE": "false",
        }
        for k, v in settings_seed.items():
            s = db.query(SystemSetting).filter(SystemSetting.key == k).first()
            if not s:
                db.add(SystemSetting(key=k, value=v))

        db.commit()
        print("Seed complete. Admin: admin@sentinelops.dev / admin123 (dev only)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
