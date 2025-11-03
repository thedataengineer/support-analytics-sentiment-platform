"""
Sync existing database records to Elasticsearch for RAG functionality
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal, get_db
from backend.models.ticket import Ticket
from backend.models.sentiment_result import SentimentResult
from backend.models.entity import Entity
from backend.services.elasticsearch_client import es_client
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_tickets_to_elasticsearch():
    """
    Sync all tickets from PostgreSQL to Elasticsearch for RAG search
    """
    if not es_client.enabled:
        logger.error("Elasticsearch is not enabled. Cannot sync.")
        return

    db = SessionLocal()
    try:
        # Get all unique tickets with their ultimate sentiment
        tickets_query = (
            db.query(
                Ticket.ticket_id,
                Ticket.summary,
                Ticket.description,
                Ticket.ultimate_sentiment,
                Ticket.ultimate_confidence,
                Ticket.created_at
            )
            .distinct(Ticket.ticket_id)
        )

        total_tickets = tickets_query.count()
        logger.info(f"Found {total_tickets} tickets to sync to Elasticsearch")

        synced_count = 0
        batch_size = 50

        for offset in range(0, total_tickets, batch_size):
            tickets = tickets_query.offset(offset).limit(batch_size).all()

            for ticket in tickets:
                # Get entities for this ticket
                entities_query = (
                    db.query(Entity.text, Entity.label)
                    .filter(Entity.ticket_id == ticket.ticket_id)
                    .distinct(Entity.text, Entity.label)
                )

                entities_list = [
                    {"text": entity.text, "type": entity.label}
                    for entity in entities_query.all()
                ]

                # Index in Elasticsearch
                try:
                    es_client.index_ticket({
                        "ticket_id": ticket.ticket_id,
                        "summary": ticket.summary or "",
                        "description": ticket.description or "",
                        "ultimate_sentiment": ticket.ultimate_sentiment,
                        "confidence": ticket.ultimate_confidence,
                        "entities": entities_list,
                        "created_at": ticket.created_at.isoformat() if ticket.created_at else None
                    })
                    synced_count += 1

                    if synced_count % 10 == 0:
                        logger.info(f"Synced {synced_count}/{total_tickets} tickets")

                except Exception as e:
                    logger.error(f"Failed to index ticket {ticket.ticket_id}: {e}")

        logger.info(f"✅ Successfully synced {synced_count} tickets to Elasticsearch")

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting Elasticsearch sync...")
    sync_tickets_to_elasticsearch()
    logger.info("Sync complete!")
