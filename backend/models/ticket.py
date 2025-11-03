from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True)  # External ticket ID
    summary = Column(Text)
    description = Column(Text)
    status = Column(String(20), default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # New fields for enhanced sentiment tracking
    issue_type = Column(String(100))
    parent_ticket_id = Column(String(50), index=True)
    ultimate_sentiment = Column(String(20), index=True)
    ultimate_confidence = Column(Float)
    sentiment_trend = Column(String(20))
    comment_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<Ticket(ticket_id={self.ticket_id}, summary={self.summary[:50]}...)>"
