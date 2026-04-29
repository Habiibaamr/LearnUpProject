"""
Synchronize existing database rows with the new ``super_admins`` table.

Run from the backend folder:
    python app/sync_super_admins.py

What it does:
1. Ensures all ORM tables exist.
2. Finds users with role == "super_admin".
3. Creates missing ``super_admins`` rows for those users.
4. Removes conflicting rows from ``admins`` for the same users.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: E402, F401
from app.core.security import ROLE_SUPER_ADMIN  # noqa: E402
from app.models.admin import Admin  # noqa: E402
from app.models.super_admin import SuperAdmin  # noqa: E402
from app.models.user import User  # noqa: E402


def sync_super_admins() -> int:
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    created = 0
    removed_admin_profiles = 0
    try:
        users = session.query(User).filter(User.role == ROLE_SUPER_ADMIN).all()
        for user in users:
            admin_profile = session.query(Admin).filter(Admin.user_id == user.id).first()
            if admin_profile is not None:
                session.delete(admin_profile)
                removed_admin_profiles += 1

            super_admin_profile = (
                session.query(SuperAdmin).filter(SuperAdmin.user_id == user.id).first()
            )
            if super_admin_profile is None:
                session.add(
                    SuperAdmin(
                        user_id=user.id,
                        position="Super Admin",
                    )
                )
                created += 1

        session.commit()
        print(
            f"Super admin sync complete. Created {created} super_admin rows and removed "
            f"{removed_admin_profiles} conflicting admin rows."
        )
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(sync_super_admins())
