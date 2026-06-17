"""
Promote an existing user to the super admin role.

Run from the backend folder, for example:
    python app/promote_super_admin.py --email admin@learnup.edu
    python app/promote_super_admin.py --user-id 1 --position "Super Admin"
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import ROLE_SUPER_ADMIN  # noqa: E402
from app.models.admin import Admin  # noqa: E402
from app.models.super_admin import SuperAdmin  # noqa: E402
from app.models.user import User  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote an existing user to super admin.")
    parser.add_argument("--user-id", type=int, default=None, help="Existing user id")
    parser.add_argument("--email", type=str, default=None, help="Existing user email")
    parser.add_argument(
        "--university-id",
        type=str,
        default=None,
        help="Existing university id",
    )
    parser.add_argument(
        "--position",
        type=str,
        default="Super Admin",
        help="Admin profile position label",
    )
    args = parser.parse_args()

    identifiers = [args.user_id is not None, bool(args.email), bool(args.university_id)]
    if sum(identifiers) != 1:
        parser.error("Pass exactly one of --user-id, --email, or --university-id.")
    return args


def main() -> int:
    args = parse_args()
    session = SessionLocal()
    try:
        query = session.query(User)
        if args.user_id is not None:
            user = query.filter(User.id == args.user_id).first()
        elif args.email:
            user = query.filter(User.email == args.email).first()
        else:
            user = query.filter(User.university_id == args.university_id).first()

        if user is None:
            print("User not found.")
            return 1

        user.role = ROLE_SUPER_ADMIN
        user.is_active = True

        admin_profile = session.query(Admin).filter(Admin.user_id == user.id).first()
        if admin_profile is not None:
            session.delete(admin_profile)

        super_admin_profile = (
            session.query(SuperAdmin).filter(SuperAdmin.user_id == user.id).first()
        )
        if super_admin_profile is None:
            super_admin_profile = SuperAdmin(
                user_id=user.id,
                position=args.position,
            )
            session.add(super_admin_profile)
        elif args.position:
            super_admin_profile.position = args.position

        session.commit()
        print(
            f"User {user.id} ({user.email}) promoted to {ROLE_SUPER_ADMIN} successfully."
        )
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
