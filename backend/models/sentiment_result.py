from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), index=True)
    text = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=False, index=True)  # positive, negative, neutral
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # New fields for temporal tracking
    field_type = Column(String(20), index=True)  # summary, description, comment
    comment_number = Column(Integer)  # 1, 2, 3... for chronological order
    comment_timestamp = Column(DateTime(timezone=True), index=True)  # parsed from comment
    author_id = Column(String(100))  # extracted from comment

    def __repr__(self):
        return f"<SentimentResult(ticket_id={self.ticket_id}, sentiment={self.sentiment})>"
