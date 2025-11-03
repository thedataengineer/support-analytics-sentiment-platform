#!/usr/bin/env python3
"""
Bootstrap the relational database used by the backend.
Creates tables and ensures a default admin account exists.
"""
import sys
import os
import logging

from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.database import init_database, check_database_connection, SessionLocal
from backend.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def create_default_user() -> None:
    """Create a default admin account if one is not present."""
    db: Session = SessionLocal()

    try:
        existing_user = db.query(User).filter(User.email == "admin@example.com").first()

        if existing_user:
            logger.info("ℹ️  Admin user already exists")
            return

        admin_user = User(
            email="admin@example.com",
            hashed_password=pwd_context.hash("password"),
            role="admin",
            is_active="Y",
        )
        db.add(admin_user)
        db.commit()
        logger.info("✅ Created default admin user (admin@example.com / password)")
    except Exception as exc:
        db.rollback()
        logger.error("❌ Failed to create default user: %s", exc)
        raise
    finally:
        db.close()


def main() -> int:
    logger.info("🚀 Starting database migration...")

    logger.info("Testing database connection...")
    if not check_database_connection():
        logger.error("❌ Database connection failed!")
        return 1

    logger.info("✅ Database connection successful")

    logger.info("Creating database tables...")
    try:
        init_database()
        logger.info("✅ Database tables created successfully")
    except Exception as exc:
        logger.error("❌ Failed to create tables: %s", exc)
        return 1

    logger.info("Ensuring default admin user exists...")
    try:
        create_default_user()
    except Exception as exc:
        logger.error("❌ Failed to create admin user: %s", exc)
        return 1

    logger.info("🎉 Database migration completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
