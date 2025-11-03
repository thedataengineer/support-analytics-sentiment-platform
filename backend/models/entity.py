from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), index=True)
    text = Column(String(100), nullable=False)  # The entity text
    label = Column(String(50), nullable=False)  # PRODUCT, ORG, PERSON, etc.
    start_pos = Column(Integer, nullable=False)  # Start position in text
    end_pos = Column(Integer, nullable=False)    # End position in text
    confidence = Column(JSON)  # Additional metadata if needed

    def __repr__(self):
        return f"<Entity(ticket_id={self.ticket_id}, text={self.text}, label={self.label})>"
