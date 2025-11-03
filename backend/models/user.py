from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), default="viewer", nullable=False)  # admin, analyst, viewer
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(String(1), default="Y", nullable=False)

    def __repr__(self):
        return f"<User(email={self.email}, role={self.role})>"
