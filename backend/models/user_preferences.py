from __future__ import annotations

from datetime import time

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base


class UserReportPreference(Base):
    """
    Stores scheduled-report delivery preferences per user.
    """

    __tablename__ = "user_report_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    schedule_frequency = Column(Enum("daily", "weekly", name="report_schedule_frequency"), nullable=False)
    delivery_time = Column(Time, nullable=False, default=time(8, 0))
    email = Column(String(255), nullable=False)
    last_sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", backref="report_preference", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_report_preference_user"),
    )
