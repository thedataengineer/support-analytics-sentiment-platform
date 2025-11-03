"""Parquet schema definitions for sentiment analysis data."""
import pyarrow as pa

# Core sentiment analysis schema
sentiment_schema = pa.schema([
    ('ticket_id', pa.string()),
    ('text', pa.string()),
    ('sentiment', pa.string()),
    ('confidence', pa.float64()),
    ('field_type', pa.string()),
    ('timestamp', pa.timestamp('us'))
])

# Ticket metadata schema
ticket_schema = pa.schema([
    ('ticket_id', pa.string()),
    ('created_date', pa.timestamp('us')),
    ('status', pa.string()),
    ('priority', pa.string()),
    ('assignee', pa.string()),
    ('reporter', pa.string()),
    ('summary', pa.string()),
    ('description', pa.string()),
    ('overall_sentiment', pa.string()),
    ('sentiment_confidence', pa.float64())
])

# Named entity recognition schema
entity_schema = pa.schema([
    ('ticket_id', pa.string()),
    ('entity_text', pa.string()),
    ('entity_type', pa.string()),
    ('confidence', pa.float64()),
    ('start_pos', pa.int32()),
    ('end_pos', pa.int32()),
    ('field_name', pa.string())
])