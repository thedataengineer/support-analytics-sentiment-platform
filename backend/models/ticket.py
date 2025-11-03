from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Ticket(Base):
    """
    Core ticket metadata persisted in PostgreSQL.
    """

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="open", server_default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    issue_type = Column(String(100), nullable=True)
    parent_ticket_id = Column(String(50), nullable=True)
    ultimate_sentiment = Column(String(20), nullable=True)
    ultimate_confidence = Column(Float, nullable=True)
    sentiment_trend = Column(String(20), nullable=True)
    comment_count = Column(Integer, nullable=False, default=0, server_default="0")

    sentiment_results = relationship(
        "SentimentResult",
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    entities = relationship(
        "Entity",
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_tickets_ticket_id", "ticket_id"),
        Index("idx_tickets_created_at", "created_at"),
        Index("idx_tickets_status", "status"),
        Index("idx_tickets_parent_ticket_id", "parent_ticket_id"),
        Index("idx_tickets_ultimate_sentiment", "ultimate_sentiment"),
    )

    def __repr__(self) -> str:
        return (
            f"<Ticket(ticket_id={self.ticket_id}, status={self.status}, "
            f"ultimate_sentiment={self.ultimate_sentiment})>"
        )
