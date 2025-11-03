#!/usr/bin/env python3
"""
Performance benchmark script for Parquet + DuckDB migration.
Tests query performance and memory usage.
"""

import time
import psutil
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.append('backend')

from backend.storage.storage_manager import StorageManager

def measure_performance(func, *args, **kwargs):
    """Measure execution time and memory usage of a function."""
    process = psutil.Process()
    
    # Get initial memory
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Execute function
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    # Get final memory
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    return {
        'execution_time': end_time - start_time,
        'memory_used': final_memory - initial_memory,
        'result_size': len(result) if hasattr(result, '__len__') else 0,
        'result': result
    }

def benchmark_queries():
    """Benchmark common query patterns."""
    print("🚀 Starting Parquet + DuckDB Performance Benchmark\n")
    
    storage = StorageManager()
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    benchmarks = []
    
    # Test 1: Sentiment Overview Query
    print("📊 Testing sentiment overview query...")
    try:
        perf = measure_performance(storage.get_sentiment_summary)
        benchmarks.append({
            'query': 'Sentiment Overview',
            'time': perf['execution_time'],
            'memory': perf['memory_used'],
            'rows': perf['result_size']
        })
        print(f"   ✅ {perf['execution_time']:.3f}s, {perf['memory_used']:.1f}MB, {perf['result_size']} rows")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Search Query
    print("🔍 Testing search query...")
    try:
        perf = measure_performance(storage.search_tickets, "error", 100)
        benchmarks.append({
            'query': 'Search Tickets',
            'time': perf['execution_time'],
            'memory': perf['memory_used'],
            'rows': perf['result_size']
        })
        print(f"   ✅ {perf['execution_time']:.3f}s, {perf['memory_used']:.1f}MB, {perf['result_size']} rows")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Complex Analytics Query
    print("📈 Testing complex analytics query...")
    try:
        analytics_sql = f"""
        SELECT 
            sentiment,
            field_type,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence
        FROM sentiment_data 
        WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
        GROUP BY sentiment, field_type
        ORDER BY count DESC
        """
        
        perf = measure_performance(
            storage.execute_query, 
            analytics_sql, 
            {'sentiment_data': 'sentiment/data.parquet'}
        )
        benchmarks.append({
            'query': 'Complex Analytics',
            'time': perf['execution_time'],
            'memory': perf['memory_used'],
            'rows': perf['result_size']
        })
        print(f"   ✅ {perf['execution_time']:.3f}s, {perf['memory_used']:.1f}MB, {perf['result_size']} rows")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Cache Performance (repeat same query)
    print("💾 Testing query cache performance...")
    try:
        # First execution (cache miss)
        perf1 = measure_performance(storage.get_sentiment_summary)
        # Second execution (cache hit)
        perf2 = measure_performance(storage.get_sentiment_summary)
        
        speedup = perf1['execution_time'] / perf2['execution_time'] if perf2['execution_time'] > 0 else 0
        benchmarks.append({
            'query': 'Cache Hit',
            'time': perf2['execution_time'],
            'memory': perf2['memory_used'],
            'rows': perf2['result_size']
        })
        print(f"   ✅ Cache speedup: {speedup:.1f}x ({perf1['execution_time']:.3f}s → {perf2['execution_time']:.3f}s)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    print(f"\n📋 Performance Summary:")
    print(f"{'Query':<20} {'Time (s)':<10} {'Memory (MB)':<12} {'Rows':<8}")
    print("-" * 52)
    
    for bench in benchmarks:
        print(f"{bench['query']:<20} {bench['time']:<10.3f} {bench['memory']:<12.1f} {bench['rows']:<8}")
    
    # Performance targets
    avg_time = sum(b['time'] for b in benchmarks) / len(benchmarks) if benchmarks else 0
    max_memory = max(b['memory'] for b in benchmarks) if benchmarks else 0
    
    print(f"\n🎯 Performance Targets:")
    print(f"   Average query time: {avg_time:.3f}s (target: <1.0s)")
    print(f"   Peak memory usage: {max_memory:.1f}MB (target: <500MB)")
    
    if avg_time < 1.0 and max_memory < 500:
        print("   🎉 All performance targets met!")
    else:
        print("   ⚠️  Some targets not met - consider further optimization")

if __name__ == "__main__":
    benchmark_queries()