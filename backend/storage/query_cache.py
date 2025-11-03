"""Query caching for DuckDB to improve performance."""
import hashlib
import pickle
import time
from typing import Any, Optional
import pandas as pd

class QueryCache:
    """Simple in-memory cache for DuckDB query results."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, sql: str, table_mappings: dict = None) -> str:
        """Generate cache key from SQL and table mappings."""
        content = f"{sql}:{str(table_mappings or {})}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, sql: str, table_mappings: dict = None) -> Optional[pd.DataFrame]:
        """Get cached query result if available and not expired."""
        key = self._generate_key(sql, table_mappings)
        
        if key not in self.cache:
            return None
        
        # Check if expired
        if time.time() - self.access_times[key] > self.ttl_seconds:
            del self.cache[key]
            del self.access_times[key]
            return None
        
        # Update access time
        self.access_times[key] = time.time()
        return self.cache[key].copy()
    
    def set(self, sql: str, result: pd.DataFrame, table_mappings: dict = None):
        """Cache query result."""
        key = self._generate_key(sql, table_mappings)
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = result.copy()
        self.access_times[key] = time.time()
    
    def clear(self):
        """Clear all cached results."""
        self.cache.clear()
        self.access_times.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)