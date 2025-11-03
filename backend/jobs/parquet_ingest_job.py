"""Parquet-based ingestion pipeline for sentiment analysis."""
import pandas as pd
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from services.column_mapping import ColumnMapper
from services.nlp_client import nlp_client
from services.comment_parser import CommentParser
from services.sentiment_aggregator import SentimentAggregator
from storage.storage_manager import StorageManager
from cache import cache
from .celery_config import celery_app
from .job_status import (
    mark_job_running,
    increment_job_progress,
    mark_job_completed,
    mark_job_failed,
    update_job_metadata,
)

logger = logging.getLogger(__name__)

class ParquetIngestPipeline:
    """Parquet-based ingestion pipeline."""
    
    def __init__(self):
        self.storage = StorageManager()
        self.mapper = ColumnMapper()
        import os
        from sqlalchemy import create_engine
        postgres_url = os.getenv('POSTGRES_URL', 'postgresql://sentiment_user:sentiment_pass@localhost:5432/sentiment_platform')
        self.engine = create_engine(postgres_url, pool_pre_ping=True)
    
    def process_csv_content(self, csv_content: str, job_id: str, filename: str) -> Dict[str, Any]:
        """Process CSV content and output to Parquet."""
        import io
        start_time = time.time()
        stats = {
            "job_id": job_id,
            "filename": filename,
            "total_rows": 0,
            "processed_rows": 0,
            "sentiment_records": 0,
            "entity_records": 0,
            "errors": [],
            "duration": 0
        }

        mark_job_running(job_id)
        logger.info(f"Starting Parquet CSV processing job {job_id} for file: {filename}")

        try:
            # Read CSV
            csv_io = io.StringIO(csv_content)
            df = pd.read_csv(csv_io)
            stats["total_rows"] = len(df)
            update_job_metadata(job_id, total_rows=len(df))

            # Process in batches
            batch_size = 500
            sentiment_batch = []
            ticket_batch = []
            entity_batch = []

            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                batch_results = self._process_batch(batch_df, job_id)
                
                sentiment_batch.extend(batch_results["sentiment_results"])
                ticket_batch.extend(batch_results["ticket_results"])
                entity_batch.extend(batch_results["entity_results"])
                
                stats["processed_rows"] += batch_results["processed_rows"]
                stats["sentiment_records"] += len(batch_results["sentiment_results"])
                stats["entity_records"] += len(batch_results["entity_results"])
                
                increment_job_progress(
                    job_id,
                    processed=batch_results["processed_rows"],
                    sentiment_records=len(batch_results["sentiment_results"]),
                    entity_records=len(batch_results["entity_results"])
                )

            # Write batches to PostgreSQL
            if sentiment_batch:
                self._write_to_postgres('sentiment_results', sentiment_batch)
            if ticket_batch:
                self._write_to_postgres('tickets', ticket_batch)
            if entity_batch:
                self._write_to_postgres('entities', entity_batch)

            # Clear cache if available
            try:
                cache.clear_pattern("sentiment_*")
            except:
                pass

            stats["duration"] = time.time() - start_time
            logger.info(f"Job {job_id} completed in {stats['duration']:.2f}s")

            mark_job_completed(
                job_id,
                records_processed=stats["processed_rows"],
                sentiment_records=stats["sentiment_records"],
                entity_records=stats["entity_records"],
                duration=stats["duration"],
                errors=stats["errors"]
            )

            return stats

        except Exception as e:
            stats["duration"] = time.time() - start_time
            error_msg = f"Job {job_id} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            stats["errors"].append(str(e))

            mark_job_failed(
                job_id,
                str(e),
                records_processed=stats["processed_rows"],
                sentiment_records=stats["sentiment_records"],
                entity_records=stats["entity_records"],
                duration=stats["duration"]
            )
            raise

    def _process_batch(self, batch_df: pd.DataFrame, job_id: str) -> Dict[str, List]:
        """Process a batch of data and return results."""
        mapping_name = f"upload_{job_id}"
        mapping = self.mapper.get_mapping(mapping_name)
        if not mapping:
            mapping = self.mapper.create_mapping(list(batch_df.columns), mapping_name)

        # Apply mapping
        filtered_batch = self.mapper.apply_mapping(batch_df, mapping)
        text_columns = mapping.get("text_columns", [])
        comment_columns = mapping.get("comment_columns", [])
        id_column = mapping.get("id_column")

        sentiment_results = []
        ticket_results = []
        entity_results = []
        processed_rows = 0

        for idx, row in filtered_batch.iterrows():
            try:
                ticket_id = str(row.get(id_column, f"TICKET-{job_id}-{idx}"))
                
                # Extract text fields
                summary = str(row.get(text_columns[0], "")).strip() if text_columns else ""
                description = str(row.get(text_columns[1], "")).strip() if len(text_columns) > 1 else ""
                
                # Process ticket metadata
                ticket_data = {
                    "ticket_id": ticket_id,
                    "created_date": datetime.utcnow(),
                    "status": str(row.get("Status", "")).strip(),
                    "priority": str(row.get("Priority", "")).strip(),
                    "assignee": str(row.get("Assignee", "")).strip(),
                    "reporter": str(row.get("Reporter", "")).strip(),
                    "summary": summary,
                    "description": description,
                    "overall_sentiment": "neutral",
                    "sentiment_confidence": 0.5
                }
                
                # Collect sentiment results for aggregation
                all_sentiments = []

                # Analyze summary
                if summary:
                    sentiment_result = self._analyze_text(summary)
                    sentiment_results.append({
                        "ticket_id": ticket_id,
                        "text": summary,
                        "sentiment": sentiment_result["sentiment"],
                        "confidence": sentiment_result["confidence"],
                        "field_type": "summary",
                        "timestamp": datetime.utcnow()
                    })
                    all_sentiments.append(sentiment_result)

                # Analyze description
                if description:
                    sentiment_result = self._analyze_text(description)
                    sentiment_results.append({
                        "ticket_id": ticket_id,
                        "text": description,
                        "sentiment": sentiment_result["sentiment"],
                        "confidence": sentiment_result["confidence"],
                        "field_type": "description",
                        "timestamp": datetime.utcnow()
                    })
                    all_sentiments.append(sentiment_result)

                # Analyze comments
                comment_count = 0
                for comment_col in comment_columns:
                    comment_text = row.get(comment_col)
                    if pd.isna(comment_text) or not str(comment_text).strip():
                        continue

                    parsed = CommentParser.parse(str(comment_text))
                    if not parsed['text'].strip():
                        continue

                    comment_count += 1
                    sentiment_result = self._analyze_text(parsed['text'])
                    sentiment_results.append({
                        "ticket_id": ticket_id,
                        "text": parsed['text'],
                        "sentiment": sentiment_result["sentiment"],
                        "confidence": sentiment_result["confidence"],
                        "field_type": "comment",
                        "timestamp": parsed['timestamp'] or datetime.utcnow()
                    })
                    all_sentiments.append(sentiment_result)

                # Calculate overall sentiment
                if all_sentiments:
                    overall_sentiment, overall_confidence, _ = SentimentAggregator.calculate_ultimate(
                        all_sentiments, strategy='weighted_recent'
                    )
                    ticket_data["overall_sentiment"] = overall_sentiment
                    ticket_data["sentiment_confidence"] = overall_confidence

                ticket_results.append(ticket_data)

                # Entity extraction
                combined_text = f"{summary} {description}".strip()
                if combined_text:
                    entities = self._extract_entities(combined_text, ticket_id)
                    entity_results.extend(entities)

                processed_rows += 1

            except Exception as e:
                logger.warning(f"Failed to process row {idx}: {e}")
                continue

        return {
            "sentiment_results": sentiment_results,
            "ticket_results": ticket_results,
            "entity_results": entity_results,
            "processed_rows": processed_rows
        }

    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        try:
            return nlp_client.get_sentiment(text)
        except Exception:
            return {"sentiment": "neutral", "confidence": 0.3}

    def _extract_entities(self, text: str, ticket_id: str) -> List[Dict]:
        """Extract entities from text."""
        try:
            entities = nlp_client.get_entities(text[:5000])
            return [
                {
                    "ticket_id": ticket_id,
                    "entity_text": entity.get("text", ""),
                    "entity_type": entity.get("label", ""),
                    "confidence": entity.get("confidence", 0.5),
                    "start_pos": entity.get("start", 0),
                    "end_pos": entity.get("end", 0),
                    "field_name": "combined"
                }
                for entity in entities
                if len(entity.get("text", "")) <= 500
            ]
        except Exception:
            return []
    
    def _write_to_postgres(self, table_name: str, data: List[Dict]):
        """Write data directly to PostgreSQL table."""
        if not data:
            return

        df = pd.DataFrame(data)

        # Create tables if not exist
        with self.engine.connect() as conn:
            if table_name == 'tickets':
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tickets (
                        ticket_id VARCHAR PRIMARY KEY,
                        created_date TIMESTAMP,
                        status VARCHAR,
                        priority VARCHAR,
                        assignee VARCHAR,
                        reporter VARCHAR,
                        summary TEXT,
                        description TEXT,
                        overall_sentiment VARCHAR,
                        sentiment_confidence FLOAT
                    )
                """)
                conn.commit()
            elif table_name == 'sentiment_results':
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sentiment_results (
                        id SERIAL PRIMARY KEY,
                        ticket_id VARCHAR,
                        text TEXT,
                        sentiment_label VARCHAR,
                        sentiment_score FLOAT,
                        field_type VARCHAR,
                        timestamp TIMESTAMP,
                        comment_number INTEGER,
                        author_id VARCHAR
                    )
                """)
                conn.commit()
            elif table_name == 'entities':
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS entities (
                        id SERIAL PRIMARY KEY,
                        ticket_id VARCHAR,
                        entity_text VARCHAR,
                        entity_type VARCHAR,
                        confidence FLOAT,
                        start_pos INTEGER,
                        end_pos INTEGER,
                        field_name VARCHAR
                    )
                """)
                conn.commit()

        # Map DataFrame columns to match table schema and handle missing columns
        if table_name == 'sentiment_results':
            df = df.rename(columns={
                'sentiment': 'sentiment_label',
                'confidence': 'sentiment_score'
            })
            # Add missing columns with default values if they don't exist
            if 'comment_number' not in df.columns:
                df['comment_number'] = None
            if 'author_id' not in df.columns:
                df['author_id'] = None
            if 'timestamp' not in df.columns:
                df['timestamp'] = pd.Timestamp.now()

        # Select only columns that exist in the table schema
        if table_name == 'sentiment_results':
            expected_cols = ['ticket_id', 'text', 'sentiment_label', 'sentiment_score', 'field_type', 'timestamp', 'comment_number', 'author_id']
            df = df[[col for col in expected_cols if col in df.columns]]
        elif table_name == 'tickets':
            expected_cols = ['ticket_id', 'created_date', 'status', 'priority', 'assignee', 'reporter', 'summary', 'description', 'overall_sentiment', 'sentiment_confidence']
            df = df[[col for col in expected_cols if col in df.columns]]
        elif table_name == 'entities':
            expected_cols = ['ticket_id', 'entity_text', 'entity_type', 'confidence', 'start_pos', 'end_pos', 'field_name']
            df = df[[col for col in expected_cols if col in df.columns]]

        # Insert data using pandas to_sql (handles conflicts automatically)
        df.to_sql(table_name, self.engine, if_exists='append', index=False, method='multi', chunksize=500)

# Celery tasks
@celery_app.task(name="backend.jobs.parquet_ingest_job.process_csv_content_parquet_task")
def process_csv_content_parquet_task(csv_content: str, job_id: str, filename: str) -> Dict[str, Any]:
    """Celery task for Parquet-based CSV processing."""
    pipeline = ParquetIngestPipeline()
    return pipeline.process_csv_content(csv_content, job_id, filename)

@celery_app.task(name="backend.jobs.parquet_ingest_job.process_json_ingest_parquet_task")
def process_json_ingest_parquet_task(job_id: str, records: List[Dict]) -> Dict[str, Any]:
    """Celery task for Parquet-based JSON processing."""
    pipeline = ParquetIngestPipeline()
    
    start_time = time.time()
    mark_job_running(job_id)
    
    try:
        sentiment_batch = []
        ticket_batch = []
        entity_batch = []
        
        for idx, record in enumerate(records):
            ticket_id = record.get('id', f'JSON-{job_id}-{idx}')
            summary = str(record.get('summary', '')).strip()
            description = str(record.get('description', '')).strip()
            
            # Process ticket
            ticket_data = {
                "ticket_id": ticket_id,
                "created_date": datetime.utcnow(),
                "summary": summary,
                "description": description,
                "overall_sentiment": "neutral",
                "sentiment_confidence": 0.5
            }
            
            all_sentiments = []
            
            # Analyze summary and description
            for text, field_type in [(summary, "summary"), (description, "description")]:
                if text:
                    sentiment_result = pipeline._analyze_text(text)
                    sentiment_batch.append({
                        "ticket_id": ticket_id,
                        "text": text,
                        "sentiment": sentiment_result["sentiment"],
                        "confidence": sentiment_result["confidence"],
                        "field_type": field_type,
                        "timestamp": datetime.utcnow()
                    })
                    all_sentiments.append(sentiment_result)
            
            # Process comments
            for comment_idx, comment_text in enumerate(record.get('comments', []), 1):
                if comment_text:
                    sentiment_result = pipeline._analyze_text(str(comment_text))
                    sentiment_batch.append({
                        "ticket_id": ticket_id,
                        "text": str(comment_text),
                        "sentiment": sentiment_result["sentiment"],
                        "confidence": sentiment_result["confidence"],
                        "field_type": "comment",
                        "timestamp": datetime.utcnow()
                    })
                    all_sentiments.append(sentiment_result)
            
            # Calculate overall sentiment
            if all_sentiments:
                overall_sentiment, overall_confidence, _ = SentimentAggregator.calculate_ultimate(
                    all_sentiments, strategy='weighted_recent'
                )
                ticket_data["overall_sentiment"] = overall_sentiment
                ticket_data["sentiment_confidence"] = overall_confidence
            
            ticket_batch.append(ticket_data)
            
            # Entity extraction
            combined_text = f"{summary} {description}".strip()
            if combined_text:
                entities = pipeline._extract_entities(combined_text, ticket_id)
                entity_batch.extend(entities)
        
        # Save to PostgreSQL
        if sentiment_batch:
            pipeline._write_to_postgres('sentiment_results', sentiment_batch)
        if ticket_batch:
            pipeline._write_to_postgres('tickets', ticket_batch)
        if entity_batch:
            pipeline._write_to_postgres('entities', entity_batch)
        
        duration = time.time() - start_time
        mark_job_completed(
            job_id,
            records_processed=len(records),
            sentiment_records=len(sentiment_batch),
            entity_records=len(entity_batch),
            duration=duration
        )
        
        return {
            "job_id": job_id,
            "processed_rows": len(records),
            "sentiment_records": len(sentiment_batch),
            "entity_records": len(entity_batch),
            "duration": duration
        }
        
    except Exception as e:
        mark_job_failed(job_id, str(e))
        raise