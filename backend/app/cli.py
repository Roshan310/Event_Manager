import argparse
import getpass

from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User, UserRole


def create_admin(email: str, name: str) -> None:
    password = getpass.getpass("Admin password: ")
    if len(password) < 10:
        raise SystemExit("Password must contain at least 10 characters")
    with SessionLocal() as db:
        db.add(
            User(
                email=email.strip().casefold(),
                name=name.strip(),
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
            )
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise SystemExit("A user with this email already exists") from exc
    print("Administrator created")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("create-admin")
    command.add_argument("--email", required=True)
    command.add_argument("--name", required=True)
    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin(args.email, args.name)


if __name__ == "__main__":
    main()
