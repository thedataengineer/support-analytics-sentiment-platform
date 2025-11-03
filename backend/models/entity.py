from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON, TypeDecorator

try:
    from sqlalchemy.dialects.postgresql import JSONB  # type: ignore
except ImportError:  # pragma: no cover
    JSONB = None


class JSONBCompat(TypeDecorator):
    """
    Provides JSONB on PostgreSQL while remaining compatible with SQLite/tests.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if JSONB is not None and dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

from database import Base


class Entity(Base):
    """
    Named entity recognition output tied to tickets.
    """

    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(
        String(50),
        ForeignKey("tickets.ticket_id", ondelete="CASCADE"),
        nullable=False,
    )
    text = Column(String(100), nullable=False)
    label = Column(String(50), nullable=False)
    start_pos = Column(Integer, nullable=False)
    end_pos = Column(Integer, nullable=False)
    confidence = Column(JSONBCompat, nullable=True)

    ticket = relationship(
        "Ticket",
        back_populates="entities",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_entities_ticket_id", "ticket_id"),
        Index("idx_entities_label", "label"),
        Index("idx_entities_text", "text"),
    )

    def __repr__(self) -> str:
        return f"<Entity(ticket_id={self.ticket_id}, label={self.label}, text={self.text})>"
