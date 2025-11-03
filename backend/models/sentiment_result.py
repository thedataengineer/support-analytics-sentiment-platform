from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class SentimentResult(Base):
    """
    Stores granular sentiment analysis signals for ticket content.
    """

    __tablename__ = "sentiment_results"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(
        String(50),
        ForeignKey("tickets.ticket_id", ondelete="CASCADE"),
        nullable=False,
    )
    text = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    field_type = Column(String(20), nullable=True)
    comment_number = Column(Integer, nullable=True)
    comment_timestamp = Column(DateTime(timezone=True), nullable=True)
    author_id = Column(String(100), nullable=True)

    ticket = relationship(
        "Ticket",
        back_populates="sentiment_results",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_sentiment_results_ticket_id", "ticket_id"),
        Index("idx_sentiment_results_sentiment", "sentiment"),
        Index("idx_sentiment_results_created_at", "created_at"),
        Index("idx_sentiment_results_field_type", "field_type"),
        Index("idx_sentiment_results_comment_timestamp", "comment_timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<SentimentResult(ticket_id={self.ticket_id}, sentiment={self.sentiment}, "
            f"confidence={self.confidence})>"
        )
