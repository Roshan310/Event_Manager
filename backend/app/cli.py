import argparse
import getpass

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.schemas.user import UserRegister
from app.services.notification_service import audit


def create_admin(email: str, name: str) -> None:
    password = getpass.getpass("Admin password: ")
    try:
        request = UserRegister(email=email, name=name, password=password)
    except ValidationError as exc:
        raise SystemExit(
            "Use a valid email, 2–120 character name and 10–128 character password"
        ) from exc
    if getpass.getpass("Confirm password: ") != password:
        raise SystemExit("Passwords do not match")
    with SessionLocal() as db:
        db.add(
            User(
                email=str(request.email).casefold(),
                name=request.name,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
                email_verified=True,
            )
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise SystemExit("A user with this email already exists") from exc
    print("Administrator created")


def promote_admin(email: str) -> None:
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email.strip().casefold()).with_for_update()
        )
        if not user:
            raise SystemExit("Account does not exist; use create-admin for a new account")
        if not user.is_active:
            raise SystemExit("Account is suspended; reactivate it through an administrator first")
        user.role = UserRole.ADMIN
        user.email_verified = True
        audit(db, user, "user.cli_promoted", user.id)
        db.commit()
    print("Existing account promoted to administrator; password preserved")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("create-admin")
    command.add_argument("--email", required=True)
    command.add_argument("--name", required=True)
    promote = commands.add_parser("promote-admin")
    promote.add_argument("--email", required=True)
    maintenance = commands.add_parser("maintenance")
    maintenance.add_argument(
        "--apply", action="store_true", help="Apply cleanup; default is dry-run"
    )
    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin(args.email, args.name)
    elif args.command == "promote-admin":
        promote_admin(args.email)
    elif args.command == "maintenance":
        from app.services.maintenance_service import cleanup

        print(cleanup(args.apply))


if __name__ == "__main__":
    main()
