"""DuckDB client for querying Parquet data."""
from __future__ import annotations

import duckdb
import pandas as pd
from typing import Dict, List, Optional, Any
import os
import logging

from config import settings
from .file_store import FileStore
from .query_cache import QueryCache

logger = logging.getLogger(__name__)

class DuckDBClient:
    def __init__(self, file_store: FileStore = None):
        self.file_store = file_store or FileStore()
        # Use persistent database file for shared access between services
        self.db_path = os.getenv('DUCKDB_PATH', settings.duckdb_path)
        # Connection cache for property
        self._conn_cache = None
        self.cache = QueryCache(max_size=50, ttl_seconds=300)  # 5 minute cache

    @property
    def conn(self):
        """Get a database connection on demand."""
        if self._conn_cache is None:
            self._conn_cache = self._get_connection()
        return self._conn_cache

    def _get_connection(self):
        """Get a database connection, creating a new one each time for thread safety."""
        conn = duckdb.connect(self.db_path)
        try:
            # Performance optimizations
            conn.execute("SET threads=4")
            conn.execute("SET memory_limit='2GB'")
        except:
            pass
        return conn
    
    def query_parquet(self, sql: str, table_mappings: Dict[str, str] = None) -> pd.DataFrame:
        """Execute SQL query on Parquet files with caching."""
        # Check cache first
        cached_result = self.cache.get(sql, table_mappings)
        if cached_result is not None:
            return cached_result
        
        if table_mappings:
            for table_name, storage_key in table_mappings.items():
                path = self.file_store.get_path(storage_key)
                if not path.exists():
                    logger.warning("Skipping missing parquet source for %s: %s", table_name, storage_key)
                    continue

                self.conn.execute(
                    f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet(?)",
                    [str(path)]
                )

        result = self.conn.execute(sql).df()
        # Cache the result
        self.cache.set(sql, result, table_mappings)
        return result
    
    def get_sentiment_summary(self, ticket_ids: List[str] = None) -> pd.DataFrame:
        """Get sentiment summary for tickets."""
        where_clause = ""
        if ticket_ids:
            ids_str = "', '".join(ticket_ids)
            where_clause = f"WHERE ticket_id IN ('{ids_str}')"
        
        sql = f"""
        SELECT 
            sentiment,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence
        FROM sentiment_data 
        {where_clause}
        GROUP BY sentiment
        ORDER BY count DESC
        """
        
        return self.query_parquet(sql, {'sentiment_data': 'sentiment/data.parquet'})
    
    def get_ticket_details(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific ticket."""
        sql = f"SELECT * FROM ticket_data WHERE ticket_id = '{ticket_id}'"
        
        df = self.query_parquet(sql, {'ticket_data': 'ticket/data.parquet'})
        return df.iloc[0].to_dict() if not df.empty else None
    
    def search_tickets(self, query: str, limit: int = 100) -> pd.DataFrame:
        """Search tickets by text content."""
        sql = f"""
        SELECT DISTINCT ticket_id, text, sentiment, confidence
        FROM sentiment_data 
        WHERE text ILIKE '%{query}%'
        LIMIT {limit}
        """
        
        return self.query_parquet(sql, {'sentiment_data': 'sentiment/data.parquet'})
