"""
Elasticsearch client for full-text search and analytics.
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from elasticsearch import Elasticsearch, exceptions as es_exceptions

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Client for interacting with Elasticsearch for ticket search and analytics"""

    def __init__(self, elasticsearch_url: str = None):
        """
        Initialize Elasticsearch client.

        Args:
            elasticsearch_url: Elasticsearch connection URL
        """
        self.es_url = elasticsearch_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.enabled = False
        self.es = None

        try:
            # Elasticsearch client initialization
            # Client 9.x is compatible with server 8.x without special headers
            self.es = Elasticsearch(
                [self.es_url],
                verify_certs=False,  # For development; enable in production
                request_timeout=5
            )
            # Test connection
            info = self.es.info()
            if info:
                self.enabled = True
                logger.info(f"Elasticsearch connected successfully at {self.es_url}")
                logger.info(f"Elasticsearch version: {info['version']['number']}")
                self._ensure_indices()
            else:
                logger.warning(f"Elasticsearch connection test failed at {self.es_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Elasticsearch at {self.es_url}: {e}. Search will fall back to PostgreSQL")

    def _ensure_indices(self):
        """Create indices if they don't exist"""
        try:
            # Tickets index
            if not self.es.indices.exists(index="tickets"):
                self.es.indices.create(
                    index="tickets",
                    body={
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 0,
                            "analysis": {
                                "analyzer": {
                                    "default": {
                                        "type": "standard",
                                        "stopwords": "_english_"
                                    }
                                }
                            }
                        },
                        "mappings": {
                            "properties": {
                                "ticket_id": {"type": "keyword"},
                                "summary": {"type": "text", "analyzer": "standard"},
                                "description": {"type": "text", "analyzer": "standard"},
                                "sentiment": {"type": "keyword"},
                                "ultimate_sentiment": {"type": "keyword"},
                                "confidence": {"type": "float"},
                                "ultimate_confidence": {"type": "float"},
                                "sentiment_trend": {"type": "keyword"},
                                "created_at": {"type": "date"},
                                "issue_type": {"type": "keyword"},
                                "comment_count": {"type": "integer"},
                                "entities": {
                                    "type": "nested",
                                    "properties": {
                                        "text": {"type": "keyword"},
                                        "label": {"type": "keyword"}
                                    }
                                }
                            }
                        }
                    }
                )
                logger.info("Created 'tickets' index in Elasticsearch")
        except Exception as e:
            logger.error(f"Failed to ensure Elasticsearch indices: {e}")

    def index_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Index a ticket in Elasticsearch.

        Args:
            ticket_data: Dictionary containing ticket information

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            self.es.index(
                index="tickets",
                id=ticket_data["ticket_id"],
                body=ticket_data,
                refresh=False  # Don't refresh immediately for performance
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index ticket {ticket_data.get('ticket_id')}: {e}")
            return False

    def bulk_index_tickets(self, tickets: List[Dict[str, Any]]) -> int:
        """
        Bulk index multiple tickets.

        Args:
            tickets: List of ticket dictionaries

        Returns:
            Number of successfully indexed tickets
        """
        if not self.enabled or not tickets:
            return 0

        from elasticsearch.helpers import bulk

        actions = [
            {
                "_index": "tickets",
                "_id": ticket["ticket_id"],
                "_source": ticket
            }
            for ticket in tickets
        ]

        try:
            success, failed = bulk(self.es, actions, raise_on_error=False)
            logger.info(f"Bulk indexed {success} tickets, {len(failed)} failed")
            return success
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return 0

    def search_tickets(
        self,
        query: Optional[str] = None,
        sentiment: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        size: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search tickets with filters.

        Args:
            query: Text search query
            sentiment: Filter by sentiment
            start_date: Filter by start date
            end_date: Filter by end date
            size: Number of results
            offset: Pagination offset

        Returns:
            Search results with total count
        """
        if not self.enabled:
            return {"total": 0, "hits": []}

        must = []
        filters = []

        # Text search with multi-match
        if query:
            must.append({
                "multi_match": {
                    "query": query,
                    "fields": ["summary^2", "description", "ticket_id"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })

        # Sentiment filter
        if sentiment:
            filters.append({"term": {"ultimate_sentiment": sentiment}})

        # Date range filter
        if start_date or end_date:
            date_range = {}
            if start_date:
                date_range["gte"] = start_date.isoformat()
            if end_date:
                date_range["lte"] = end_date.isoformat()
            filters.append({"range": {"created_at": date_range}})

        # Build query
        es_query = {
            "bool": {
                "must": must if must else [{"match_all": {}}],
                "filter": filters
            }
        }

        try:
            response = self.es.search(
                index="tickets",
                body={
                    "query": es_query,
                    "from": offset,
                    "size": size,
                    "sort": [{"created_at": {"order": "desc"}}]
                }
            )

            return {
                "total": response["hits"]["total"]["value"],
                "hits": [
                    {
                        "ticket_id": hit["_source"]["ticket_id"],
                        "summary": hit["_source"].get("summary", ""),
                        "description": hit["_source"].get("description", ""),
                        "sentiment": hit["_source"].get("ultimate_sentiment", "neutral"),
                        "confidence": hit["_source"].get("ultimate_confidence", 0.5),
                        "created_at": hit["_source"].get("created_at"),
                        "score": hit["_score"]
                    }
                    for hit in response["hits"]["hits"]
                ]
            }
        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            return {"total": 0, "hits": []}

    def aggregate_entities(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Aggregate top entities from tickets.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of entities to return

        Returns:
            List of entities with counts
        """
        if not self.enabled:
            return []

        filters = []
        if start_date or end_date:
            date_range = {}
            if start_date:
                date_range["gte"] = start_date.isoformat()
            if end_date:
                date_range["lte"] = end_date.isoformat()
            filters.append({"range": {"created_at": date_range}})

        try:
            response = self.es.search(
                index="tickets",
                body={
                    "query": {
                        "bool": {
                            "filter": filters
                        }
                    },
                    "size": 0,
                    "aggs": {
                        "entities": {
                            "nested": {
                                "path": "entities"
                            },
                            "aggs": {
                                "entity_counts": {
                                    "terms": {
                                        "field": "entities.text",
                                        "size": limit,
                                        "order": {"_count": "desc"}
                                    },
                                    "aggs": {
                                        "labels": {
                                            "terms": {
                                                "field": "entities.label"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            )

            entities = []
            for bucket in response["aggregations"]["entities"]["entity_counts"]["buckets"]:
                label = bucket["labels"]["buckets"][0]["key"] if bucket["labels"]["buckets"] else "UNKNOWN"
                entities.append({
                    "text": bucket["key"],
                    "label": label,
                    "count": bucket["doc_count"]
                })

            return entities
        except Exception as e:
            logger.error(f"Entity aggregation failed: {e}")
            return []

    def refresh_index(self):
        """Force refresh of the tickets index"""
        if self.enabled:
            try:
                self.es.indices.refresh(index="tickets")
            except Exception as e:
                logger.error(f"Failed to refresh index: {e}")


# Global client instance
es_client = ElasticsearchClient()
