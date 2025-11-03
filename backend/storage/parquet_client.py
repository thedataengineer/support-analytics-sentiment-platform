"""Parquet client for read/write operations."""
from __future__ import annotations

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

from .file_store import FileStore
from .schemas import sentiment_schema, ticket_schema, entity_schema

class ParquetClient:
    def __init__(self, file_store: FileStore = None):
        self.file_store = file_store or FileStore()
        self.schemas = {
            'sentiment': sentiment_schema,
            'ticket': ticket_schema,
            'entity': entity_schema
        }
    
    def write_dataframe(self, df: pd.DataFrame, table_type: str, partition_key: str = None) -> str:
        """Write DataFrame to Parquet with optimizations and persist to storage."""
        schema = self.schemas.get(table_type)
        if not schema:
            raise ValueError(f"Unknown table type: {table_type}")
        
        # Generate partitioned key for better query performance
        now = datetime.utcnow()
        if partition_key:
            storage_key = f"{table_type}/year={now.year}/month={now.month:02d}/day={now.day:02d}/{partition_key}.parquet"
        else:
            storage_key = f"{table_type}/year={now.year}/month={now.month:02d}/day={now.day:02d}/data.parquet"

        destination = self.file_store.get_path(storage_key)
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Write to destination with optimizations
        table = pa.Table.from_pandas(df, schema=schema)
        pq.write_table(
            table,
            destination,
            compression='snappy',  # Good balance of speed/compression
            row_group_size=5000,   # Optimize for 10k row datasets
            use_dictionary=True,   # Better compression for repeated values
            write_statistics=True  # Enable predicate pushdown
        )

        return storage_key
    
    def read_dataframe(self, table_type: str, partition_key: str = None) -> Optional[pd.DataFrame]:
        """Read Parquet file from storage and return DataFrame."""
        storage_key = f"{table_type}/{partition_key or 'data'}.parquet"

        if not self.file_store.file_exists(storage_key):
            return None

        return pd.read_parquet(self.file_store.get_path(storage_key))
    
    def append_data(self, df: pd.DataFrame, table_type: str, partition_key: str = None) -> str:
        """Append data to existing Parquet file or create new one."""
        existing_df = self.read_dataframe(table_type, partition_key)
        
        if existing_df is not None:
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            combined_df = df
        
        return self.write_dataframe(combined_df, table_type, partition_key)
    
    def list_partitions(self, table_type: str) -> List[str]:
        """List available partitions for a table type."""
        prefix = f"{table_type}/"
        files = self.file_store.list_files(prefix)
        return [f.replace(prefix, '').replace('.parquet', '') for f in files]
