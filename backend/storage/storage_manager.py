"""Storage manager for Parquet-based data operations."""
from __future__ import annotations

import pandas as pd
from typing import Dict, List, Optional, Any

from .file_store import FileStore
from .parquet_client import ParquetClient
from .duckdb_client import DuckDBClient

class StorageManager:
    """Unified interface for all storage operations."""
    
    def __init__(self):
        self.file_store = FileStore()
        self.parquet_client = ParquetClient(self.file_store)
        self.duckdb_client = DuckDBClient(self.file_store)
    
    # Write operations
    def save_sentiment_results(self, results: List[Dict], partition_key: str = None) -> str:
        """Save sentiment analysis results."""
        df = pd.DataFrame(results)
        return self.parquet_client.write_dataframe(df, 'sentiment', partition_key)
    
    def save_ticket_data(self, tickets: List[Dict], partition_key: str = None) -> str:
        """Save ticket metadata."""
        df = pd.DataFrame(tickets)
        return self.parquet_client.write_dataframe(df, 'ticket', partition_key)
    
    def save_entity_data(self, entities: List[Dict], partition_key: str = None) -> str:
        """Save named entity recognition results."""
        df = pd.DataFrame(entities)
        return self.parquet_client.write_dataframe(df, 'entity', partition_key)
    
    # Read operations
    def get_sentiment_summary(self, ticket_ids: List[str] = None) -> pd.DataFrame:
        """Get sentiment distribution summary."""
        return self.duckdb_client.get_sentiment_summary(ticket_ids)
    
    def get_ticket_details(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed ticket information."""
        return self.duckdb_client.get_ticket_details(ticket_id)
    
    def search_tickets(self, query: str, limit: int = 100) -> pd.DataFrame:
        """Search tickets by content."""
        return self.duckdb_client.search_tickets(query, limit)
    
    # Custom queries
    def execute_query(self, sql: str, table_mappings: Dict[str, str] = None) -> pd.DataFrame:
        """Execute custom SQL query."""
        return self.duckdb_client.query_parquet(sql, table_mappings)
