import pandas as pd
import os
import logging
import time
from typing import Dict, Any

from services.column_mapping import ColumnMapper
from services.nlp_client import nlp_client
from services.comment_parser import CommentParser
from services.sentiment_aggregator import SentimentAggregator
from services.elasticsearch_client import es_client
from database import get_db_context
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

def process_csv_content(csv_content: str, job_id: str, filename: str) -> Dict[str, Any]:
    """
    Process CSV content for sentiment analysis

    Args:
        csv_content: CSV file content as string
        job_id: Unique job identifier
        filename: Original filename

    Returns:
        Processing statistics
    """
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
    logger.info(f"Starting CSV content processing job {job_id} for file: {filename}")

    try:
        # Initialize column mapper
        mapper = ColumnMapper()
        mapping_name = f"upload_{job_id}"

        # Read CSV from string content
        chunk_size = 500
        logger.info(f"Reading CSV content in chunks of {chunk_size} rows")

        # First, count total rows (for progress tracking)
        try:
            total_rows = len(csv_content.split('\n')) - 1  # Subtract header
            stats["total_rows"] = total_rows
            update_job_metadata(job_id, total_rows=total_rows)
            logger.info(f"CSV contains {total_rows} data rows")
        except Exception as e:
            logger.warning(f"Could not count total rows: {e}")

        # Process CSV content in chunks
        csv_io = io.StringIO(csv_content)
        chunks = pd.read_csv(csv_io, chunksize=chunk_size)
        chunk_number = 0

        with get_db_context() as db:
            for chunk in chunks:
                chunk_number += 1
                logger.debug(f"Processing chunk {chunk_number} with {len(chunk)} rows")

                try:
                    chunk_stats = process_chunk(chunk, mapper, db, job_id, mapping_name)
                    stats["processed_rows"] += chunk_stats["processed_rows"]
                    stats["sentiment_records"] += chunk_stats["sentiment_records"]
                    stats["entity_records"] += chunk_stats["entity_records"]

                    if chunk_stats["errors"]:
                        stats["errors"].extend(chunk_stats["errors"])

                    increment_job_progress(
                        job_id,
                        processed=chunk_stats["processed_rows"],
                        sentiment_records=chunk_stats["sentiment_records"],
                        entity_records=chunk_stats["entity_records"],
                    )

                except Exception as e:
                    error_msg = f"Failed to process chunk {chunk_number}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

        # Clear relevant cache after processing
        cache.clear_pattern("sentiment_*")
        logger.info("Cleared sentiment-related cache entries")

        stats["duration"] = time.time() - start_time
        logger.info(f"Job {job_id} completed successfully in {stats['duration']:.2f}s. "
                   f"Processed {stats['processed_rows']} rows, "
                   f"created {stats['sentiment_records']} sentiment records, "
                   f"{stats['entity_records']} entity records")

        mark_job_completed(
            job_id,
            records_processed=stats["processed_rows"],
            sentiment_records=stats["sentiment_records"],
            entity_records=stats["entity_records"],
            duration=stats["duration"],
            errors=stats["errors"],
        )

        return stats

    except Exception as e:
        stats["duration"] = time.time() - start_time
        error_msg = f"Job {job_id} failed after {stats['duration']:.2f}s: {str(e)}"
        logger.error(error_msg, exc_info=True)
        stats["errors"].append(str(e))

        mark_job_failed(
            job_id,
            str(e),
            records_processed=stats["processed_rows"],
            sentiment_records=stats["sentiment_records"],
            entity_records=stats["entity_records"],
            duration=stats["duration"],
        )

        raise Exception(error_msg) from e

def process_csv_upload(file_path: str, job_id: str) -> Dict[str, Any]:
    """
    Process uploaded CSV file for sentiment analysis

    Args:
        file_path: Path to the uploaded CSV file
        job_id: Unique job identifier

    Returns:
        Processing statistics

    Raises:
        Exception: If processing fails
    """
    start_time = time.time()
    stats = {
        "job_id": job_id,
        "file_path": file_path,
        "total_rows": 0,
        "processed_rows": 0,
        "sentiment_records": 0,
        "entity_records": 0,
        "errors": [],
        "duration": 0
    }

    mark_job_running(job_id)
    logger.info(f"Starting CSV processing job {job_id} for file: {file_path}")

    try:
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Initialize column mapper
        mapper = ColumnMapper()
        mapping_name = f"upload_{job_id}"

        # Read CSV in chunks for memory efficiency
        chunk_size = 500
        logger.info(f"Reading CSV in chunks of {chunk_size} rows")

        # First, count total rows (for progress tracking)
        try:
            total_rows = sum(1 for _ in open(file_path, 'r', encoding='utf-8', errors='ignore')) - 1  # Subtract header
            stats["total_rows"] = total_rows
            update_job_metadata(job_id, total_rows=total_rows)
            logger.info(f"CSV contains {total_rows} data rows")
        except Exception as e:
            logger.warning(f"Could not count total rows: {e}")

        chunks = pd.read_csv(file_path, chunksize=chunk_size, encoding='utf-8')
        chunk_number = 0

        with get_db_context() as db:
            for chunk in chunks:
                chunk_number += 1
                logger.debug(f"Processing chunk {chunk_number} with {len(chunk)} rows")

                try:
                    chunk_stats = process_chunk(chunk, mapper, db, job_id, mapping_name)
                    stats["processed_rows"] += chunk_stats["processed_rows"]
                    stats["sentiment_records"] += chunk_stats["sentiment_records"]
                    stats["entity_records"] += chunk_stats["entity_records"]

                    if chunk_stats["errors"]:
                        stats["errors"].extend(chunk_stats["errors"])

                    increment_job_progress(
                        job_id,
                        processed=chunk_stats["processed_rows"],
                        sentiment_records=chunk_stats["sentiment_records"],
                        entity_records=chunk_stats["entity_records"],
                    )

                except Exception as e:
                    error_msg = f"Failed to process chunk {chunk_number}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

        # Clear relevant cache after processing
        cache.clear_pattern("sentiment_*")
        logger.info("Cleared sentiment-related cache entries")

        # Clean up file
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up file {file_path}: {e}")

        stats["duration"] = time.time() - start_time
        logger.info(f"Job {job_id} completed successfully in {stats['duration']:.2f}s. "
                   f"Processed {stats['processed_rows']} rows, "
                   f"created {stats['sentiment_records']} sentiment records, "
                   f"{stats['entity_records']} entity records")

        mark_job_completed(
            job_id,
            records_processed=stats["processed_rows"],
            sentiment_records=stats["sentiment_records"],
            entity_records=stats["entity_records"],
            duration=stats["duration"],
            errors=stats["errors"],
        )

        return stats

    except Exception as e:
        stats["duration"] = time.time() - start_time
        error_msg = f"Job {job_id} failed after {stats['duration']:.2f}s: {str(e)}"
        logger.error(error_msg, exc_info=True)
        stats["errors"].append(str(e))

        mark_job_failed(
            job_id,
            str(e),
            records_processed=stats["processed_rows"],
            sentiment_records=stats["sentiment_records"],
            entity_records=stats["entity_records"],
            duration=stats["duration"],
        )

        # Clean up file on failure
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        raise Exception(error_msg) from e


@celery_app.task(name="backend.jobs.ingest_job.process_csv_upload_task", bind=True)
def process_csv_upload_task(self, file_path: str, job_id: str) -> Dict[str, Any]:
    """
    Celery task wrapper for CSV processing.

    Args:
        file_path: Path to the uploaded CSV file
        job_id: Unique job identifier

    Returns:
        Processing statistics
    """
    return process_csv_upload(file_path, job_id)

@celery_app.task(name="backend.jobs.ingest_job.process_csv_content_task", bind=True)
def process_csv_content_task(self, csv_content: str, job_id: str, filename: str) -> Dict[str, Any]:
    """
    Celery task wrapper for CSV content processing.

    Args:
        csv_content: CSV file content as string
        job_id: Unique job identifier
        filename: Original filename

    Returns:
        Processing statistics
    """
    return process_csv_content(csv_content, job_id, filename)


@celery_app.task(name="backend.jobs.ingest_job.process_json_ingest_task", bind=True)
def process_json_ingest_task(self, job_id: str, records: list) -> Dict[str, Any]:
    """
    Celery task for processing JSON batch ingestion.

    Args:
        job_id: Unique job identifier
        records: List of record dictionaries

    Returns:
        Processing statistics
    """
    from sqlalchemy import select
    from models.sentiment_result import SentimentResult
    from models.entity import Entity
    from models.ticket import Ticket

    start_time = time.time()
    stats = {
        "job_id": job_id,
        "total_records": len(records),
        "processed_rows": 0,
        "sentiment_records": 0,
        "entity_records": 0,
        "errors": []
    }

    mark_job_running(job_id)
    logger.info(f"Starting JSON ingestion job {job_id} with {len(records)} records")

    try:
        with get_db_context() as db:
            for idx, record in enumerate(records, start=1):
                try:
                    # Get ticket ID
                    ticket_id = record.get('id', f'JSON-{job_id}-{idx}')

                    # Get text fields
                    summary = str(record.get('summary', '')).strip()
                    description = str(record.get('description', '')).strip()
                    comments = record.get('comments', [])

                    # Create or update ticket
                    existing_ticket = db.execute(
                        select(Ticket).where(Ticket.ticket_id == ticket_id)
                    ).scalar_one_or_none()

                    if existing_ticket:
                        existing_ticket.summary = summary
                        existing_ticket.description = description
                        ticket = existing_ticket
                    else:
                        ticket = Ticket(
                            ticket_id=ticket_id,
                            summary=summary,
                            description=description
                        )
                        db.add(ticket)
                        db.flush()

                    # Analyze summary
                    if summary:
                        try:
                            sentiment_result = nlp_client.get_sentiment(summary)
                            sentiment_record = SentimentResult(
                                ticket_id=ticket_id,
                                text=summary[:1000],
                                sentiment=sentiment_result.get("sentiment", "neutral"),
                                confidence=sentiment_result.get("confidence", 0.5),
                                field_type='summary'
                            )
                            db.add(sentiment_record)
                            stats["sentiment_records"] += 1
                        except Exception as e:
                            logger.warning(f"Sentiment analysis failed for summary: {e}")

                    # Analyze description
                    if description:
                        try:
                            sentiment_result = nlp_client.get_sentiment(description)
                            sentiment_record = SentimentResult(
                                ticket_id=ticket_id,
                                text=description[:1000],
                                sentiment=sentiment_result.get("sentiment", "neutral"),
                                confidence=sentiment_result.get("confidence", 0.5),
                                field_type='description'
                            )
                            db.add(sentiment_record)
                            stats["sentiment_records"] += 1
                        except Exception as e:
                            logger.warning(f"Sentiment analysis failed for description: {e}")

                    # Process comments if present
                    for comment_idx, comment_text in enumerate(comments, start=1):
                        if not comment_text or not str(comment_text).strip():
                            continue

                        try:
                            sentiment_result = nlp_client.get_sentiment(str(comment_text))
                            sentiment_record = SentimentResult(
                                ticket_id=ticket_id,
                                text=str(comment_text)[:1000],
                                sentiment=sentiment_result.get("sentiment", "neutral"),
                                confidence=sentiment_result.get("confidence", 0.5),
                                field_type='comment',
                                comment_number=comment_idx
                            )
                            db.add(sentiment_record)
                            stats["sentiment_records"] += 1
                        except Exception as e:
                            logger.warning(f"Sentiment analysis failed for comment: {e}")

                    # Entity extraction
                    combined_text = f"{summary} {description}".strip()
                    if combined_text:
                        try:
                            entities = nlp_client.get_entities(combined_text[:5000])
                            for entity_data in entities:
                                entity = Entity(
                                    ticket_id=ticket_id,
                                    text=entity_data.get("text", ""),
                                    label=entity_data.get("label", ""),
                                    start_pos=entity_data.get("start", 0),
                                    end_pos=entity_data.get("end", 0)
                                )
                                db.add(entity)
                                stats["entity_records"] += 1
                        except Exception as e:
                            logger.warning(f"Entity extraction failed: {e}")

                    stats["processed_rows"] += 1

                    # Update progress every 10 records
                    if idx % 10 == 0:
                        increment_job_progress(
                            job_id,
                            processed=10,
                            sentiment_records=stats["sentiment_records"],
                            entity_records=stats["entity_records"]
                        )

                except Exception as e:
                    error_msg = f"Failed to process record {idx}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    continue

        # Clear cache
        cache.clear_pattern("sentiment_*")

        stats["duration"] = time.time() - start_time
        logger.info(f"JSON ingestion job {job_id} completed in {stats['duration']:.2f}s")

        mark_job_completed(
            job_id,
            records_processed=stats["processed_rows"],
            sentiment_records=stats["sentiment_records"],
            entity_records=stats["entity_records"],
            duration=stats["duration"]
        )

        return stats

    except Exception as e:
        stats["duration"] = time.time() - start_time
        error_msg = f"Job {job_id} failed: {str(e)}"
        logger.error(error_msg, exc_info=True)

        mark_job_failed(
            job_id,
            str(e),
            records_processed=stats["processed_rows"],
            sentiment_records=stats["sentiment_records"],
            entity_records=stats["entity_records"],
            duration=stats["duration"]
        )

        raise


def process_chunk(chunk: pd.DataFrame, mapper: ColumnMapper, db, job_id: str, mapping_name: str) -> Dict[str, Any]:
    """
    Process a chunk of CSV data with individual comment analysis

    Returns:
        Statistics about processed chunk
    """
    from sqlalchemy import select
    from models.sentiment_result import SentimentResult
    from models.entity import Entity
    from models.ticket import Ticket
    import uuid

    stats = {
        "processed_rows": 0,
        "sentiment_records": 0,
        "entity_records": 0,
        "errors": []
    }

    try:
        mapping = mapper.get_mapping(mapping_name)
        if not mapping:
            mapping = mapper.create_mapping(list(chunk.columns), mapping_name)
            logger.debug(f"Created column mapping for {mapping_name}: {mapping}")

        # Apply mapping
        filtered_chunk = mapper.apply_mapping(chunk, mapping)
        text_columns = mapping.get("text_columns", [])
        comment_columns = mapping.get("comment_columns", [])
        id_column = mapping.get("id_column")

        if len(filtered_chunk) == 0:
            logger.warning("No rows to process after filtering")
            return stats

        for idx, row in filtered_chunk.iterrows():
            try:
                # Generate or get ticket ID
                ticket_id = str(row.get(id_column, uuid.uuid4()))

                # Extract summary and description
                summary = ""
                description = ""

                if text_columns:
                    summary = str(row.get(text_columns[0], "")).strip() if len(text_columns) > 0 else ""
                    description = str(row.get(text_columns[1], "")).strip() if len(text_columns) > 1 else ""

                # Extract parent and issue type
                parent_ticket_id = None
                issue_type = None
                if 'Parent' in row:
                    parent_val = row.get('Parent')
                    if pd.notna(parent_val):
                        parent_ticket_id = str(parent_val).strip()

                if 'Issue Type' in row:
                    issue_val = row.get('Issue Type')
                    if pd.notna(issue_val):
                        issue_type = str(issue_val).strip()

                # Create/update ticket record
                existing_ticket = db.execute(
                    select(Ticket).where(Ticket.ticket_id == ticket_id)
                ).scalar_one_or_none()

                if existing_ticket:
                    existing_ticket.summary = summary
                    existing_ticket.description = description
                    existing_ticket.issue_type = issue_type
                    existing_ticket.parent_ticket_id = parent_ticket_id
                    ticket = existing_ticket
                else:
                    ticket = Ticket(
                        ticket_id=ticket_id,
                        summary=summary,
                        description=description,
                        issue_type=issue_type,
                        parent_ticket_id=parent_ticket_id
                    )
                    db.add(ticket)
                    db.flush()

                # List to collect all sentiment results for this ticket
                sentiment_results = []

                # 1. Analyze Summary (if present)
                if summary.strip():
                    try:
                        try:
                            sentiment_result = nlp_client.get_sentiment(summary)
                        except Exception:
                            # Fallback to simple rule-based sentiment
                            sentiment_result = {"sentiment": "neutral", "confidence": 0.3}
                        
                        sentiment_record = SentimentResult(
                            ticket_id=ticket_id,
                            text=summary[:1000],  # Limit text length
                            sentiment=sentiment_result.get("sentiment", "neutral"),
                            confidence=sentiment_result.get("confidence", 0.5),
                            field_type='summary'
                        )
                        db.add(sentiment_record)
                        stats["sentiment_records"] += 1

                        sentiment_results.append({
                            'sentiment': sentiment_record.sentiment,
                            'confidence': sentiment_record.confidence,
                            'comment_number': 0  # Summary is first
                        })
                    except Exception as e:
                        logger.warning(f"Sentiment analysis failed for summary of {ticket_id}: {e}")

                # 2. Analyze Description (if present)
                if description.strip():
                    try:
                        try:
                            sentiment_result = nlp_client.get_sentiment(description)
                        except Exception:
                            sentiment_result = {"sentiment": "neutral", "confidence": 0.3}
                        
                        sentiment_record = SentimentResult(
                            ticket_id=ticket_id,
                            text=description[:1000],
                            sentiment=sentiment_result.get("sentiment", "neutral"),
                            confidence=sentiment_result.get("confidence", 0.5),
                            field_type='description'
                        )
                        db.add(sentiment_record)
                        stats["sentiment_records"] += 1

                        sentiment_results.append({
                            'sentiment': sentiment_record.sentiment,
                            'confidence': sentiment_record.confidence,
                            'comment_number': 1  # Description is second
                        })
                    except Exception as e:
                        logger.warning(f"Sentiment analysis failed for description of {ticket_id}: {e}")

                # 3. Analyze all Comments separately
                comment_count = 0
                for comment_col in comment_columns:
                    comment_text = row.get(comment_col)

                    # Skip if comment is empty or NaN
                    if pd.isna(comment_text) or not str(comment_text).strip():
                        continue

                    comment_text = str(comment_text).strip()

                    # Parse comment metadata
                    parsed = CommentParser.parse(comment_text)
                    actual_text = parsed['text']

                    if not actual_text.strip():
                        continue

                    try:
                        try:
                            sentiment_result = nlp_client.get_sentiment(actual_text)
                        except Exception:
                            sentiment_result = {"sentiment": "neutral", "confidence": 0.3}
                        
                        comment_count += 1

                        sentiment_record = SentimentResult(
                            ticket_id=ticket_id,
                            text=actual_text[:1000],
                            sentiment=sentiment_result.get("sentiment", "neutral"),
                            confidence=sentiment_result.get("confidence", 0.5),
                            field_type='comment',
                            comment_number=comment_count,
                            comment_timestamp=parsed['timestamp'],
                            author_id=parsed['author_id']
                        )
                        db.add(sentiment_record)
                        stats["sentiment_records"] += 1

                        sentiment_results.append({
                            'sentiment': sentiment_record.sentiment,
                            'confidence': sentiment_record.confidence,
                            'comment_number': comment_count + 1  # Offset by summary/description
                        })
                    except Exception as e:
                        logger.warning(f"Sentiment analysis failed for comment {comment_count} of {ticket_id}: {e}")

                # 4. Calculate ultimate sentiment from all results
                if sentiment_results:
                    try:
                        ultimate_sentiment, ultimate_confidence, sentiment_trend = \
                            SentimentAggregator.calculate_ultimate(sentiment_results, strategy='weighted_recent')

                        ticket.ultimate_sentiment = ultimate_sentiment
                        ticket.ultimate_confidence = ultimate_confidence
                        ticket.sentiment_trend = sentiment_trend
                        ticket.comment_count = comment_count
                    except Exception as e:
                        logger.warning(f"Failed to calculate ultimate sentiment for {ticket_id}: {e}")

                # 5. Entity extraction from combined text (for summary + description only)
                entities_list = []
                combined_text = f"{summary} {description}".strip()
                if combined_text:
                    try:
                        # Limit text length for entity extraction to avoid processing huge texts
                        # Entity extraction is most useful for first 5000 chars anyway
                        text_for_entities = combined_text[:5000]
                        try:
                            entities = nlp_client.get_entities(text_for_entities)
                        except Exception:
                            entities = []  # Skip entity extraction if ML service unavailable

                        for entity_data in entities:
                            entity_text = entity_data.get("text", "")
                            # Skip if entity text is too long (likely garbage extraction)
                            if len(entity_text) > 500:
                                continue

                            entity = Entity(
                                ticket_id=ticket_id,
                                text=entity_text,
                                label=entity_data.get("label", ""),
                                start_pos=entity_data.get("start", 0),
                                end_pos=entity_data.get("end", 0)
                            )
                            db.add(entity)
                            stats["entity_records"] += 1

                            # Collect for Elasticsearch indexing
                            entities_list.append({
                                "text": entity_text,
                                "label": entity_data.get("label", "")
                            })
                    except Exception as e:
                        logger.warning(f"Entity extraction failed for ticket {ticket_id}: {e}")

                # 6. Index ticket in Elasticsearch
                try:
                    es_client.index_ticket({
                        "ticket_id": ticket_id,
                        "summary": summary,
                        "description": description,
                        "ultimate_sentiment": ticket.ultimate_sentiment,
                        "ultimate_confidence": ticket.ultimate_confidence,
                        "sentiment_trend": ticket.sentiment_trend,
                        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                        "issue_type": ticket.issue_type,
                        "comment_count": comment_count,
                        "entities": entities_list
                    })
                except Exception as e:
                    logger.warning(f"Failed to index ticket {ticket_id} in Elasticsearch: {e}")

                stats["processed_rows"] += 1

            except Exception as e:
                error_msg = f"Failed to process row {idx}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                continue

        logger.debug(f"Processed chunk: {stats['processed_rows']} rows, "
                    f"{stats['sentiment_records']} sentiment records, "
                    f"{stats['entity_records']} entity records")

        return stats

    except Exception as e:
        error_msg = f"Critical error processing chunk: {str(e)}"
        logger.error(error_msg, exc_info=True)
        stats["errors"].append(error_msg)
        return stats

def process_parquet_data(df: pd.DataFrame, job_id: str) -> Dict[str, Any]:
    """Process parquet DataFrame for sentiment analysis using existing ML service"""
    
    # Initialize services
    mapper = ColumnMapper()
    
    # Create mapping for JIRA data
    mapping = mapper.create_mapping(df.columns.tolist(), 'jira')
    
    # Process full dataset
    sample_df = df
    results = []
    
    for _, row in sample_df.iterrows():
        try:
            # Get text from Summary and Description columns
            text_parts = []
            if 'Summary' in row:
                text_parts.append(str(row['Summary']))
            if 'Description' in row:
                text_parts.append(str(row['Description']))
            
            full_text = ' '.join(text_parts)
            
            if full_text.strip():
                # Use existing NLP client for sentiment analysis
                sentiment_result = nlp_client.get_sentiment(full_text)
                entities = nlp_client.get_entities(full_text)
                
                results.append({
                    'ticket_id': row.get('Issue key', f'TICKET-{len(results)}'),
                    'text': full_text[:200] + '...' if len(full_text) > 200 else full_text,
                    'sentiment': sentiment_result.get('sentiment', 'neutral'),
                    'confidence': sentiment_result.get('confidence', 0.5),
                    'entities': entities[:3]  # Top 3 entities
                })
        except Exception as e:
            logger.error(f"Error processing row: {e}")
            continue
    
    # Generate summary
    sentiments = [r['sentiment'] for r in results]
    summary = {
        'total_processed': len(results),
        'positive': sentiments.count('positive'),
        'negative': sentiments.count('negative'),
        'neutral': sentiments.count('neutral'),
        'avg_confidence': round(sum(r['confidence'] for r in results) / len(results), 3) if results else 0
    }
    
    return {
        'summary': summary,
        'sample_results': results[:10]
    }


@celery_app.task(name="backend.jobs.ingest_job.process_parquet_content_task")
def process_parquet_content_task(parquet_content: bytes, job_id: str, filename: str) -> Dict[str, Any]:
    """Process parquet content directly"""
    import io
    start_time = time.time()
    
    mark_job_running(job_id)
    
    try:
        df = pd.read_parquet(io.BytesIO(parquet_content))
        
        mapper = ColumnMapper()
        mapping_name = f"parquet_{job_id}"
        
        # Process in smaller batches for large datasets
        batch_size = 100 if len(df) > 1000 else len(df)
        
        with get_db_context() as db:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                chunk_stats = process_chunk(batch, mapper, db, job_id, mapping_name)
                
                increment_job_progress(
                    job_id,
                    processed=chunk_stats["processed_rows"],
                    sentiment_records=chunk_stats["sentiment_records"],
                    entity_records=chunk_stats["entity_records"]
                )
            
        duration = time.time() - start_time
        
        mark_job_completed(
            job_id,
            records_processed=chunk_stats["processed_rows"],
            sentiment_records=chunk_stats["sentiment_records"], 
            entity_records=chunk_stats["entity_records"],
            duration=duration
        )
        
        return chunk_stats
        
    except Exception as e:
        mark_job_failed(job_id, str(e))
        raise

@celery_app.task(name="backend.jobs.ingest_job.process_parquet_job")
def process_parquet_job(job_id: str, parquet_path: str, batch_size: int = 500) -> Dict[str, Any]:
    """
    Celery task to process a parquet source asynchronously.
    """
    start_time = time.time()
    stats = {
        "job_id": job_id,
        "file_path": parquet_path,
        "total_rows": 0,
        "processed_rows": 0,
        "sentiment_records": 0,
        "entity_records": 0,
        "errors": [],
        "duration": 0,
    }

    mark_job_running(job_id)
    logger.info(f"Starting parquet processing job {job_id} for file: {parquet_path}")

    try:
        import pyarrow.parquet as pq

        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

        parquet_file = pq.ParquetFile(parquet_path)

        total_rows = parquet_file.metadata.num_rows
        total_columns = parquet_file.metadata.num_columns
        stats["total_rows"] = total_rows
        update_job_metadata(job_id, total_rows=total_rows, total_columns=total_columns)

        mapper = ColumnMapper()
        mapping_name = f"parquet_{job_id}"
        mapper.create_mapping(list(parquet_file.schema.names), mapping_name)

        batch_number = 0
        with get_db_context() as db:
            for record_batch in parquet_file.iter_batches(batch_size=batch_size):
                batch_number += 1
                chunk = record_batch.to_pandas()

                try:
                    chunk_stats = process_chunk(chunk, mapper, db, job_id, mapping_name)
                    stats["processed_rows"] += chunk_stats["processed_rows"]
                    stats["sentiment_records"] += chunk_stats["sentiment_records"]
                    stats["entity_records"] += chunk_stats["entity_records"]

                    if chunk_stats["errors"]:
                        stats["errors"].extend(chunk_stats["errors"])

                    increment_job_progress(
                        job_id,
                        processed=chunk_stats["processed_rows"],
                        sentiment_records=chunk_stats["sentiment_records"],
                        entity_records=chunk_stats["entity_records"],
                    )

                    # Log progress for large files
                    if batch_number % 10 == 0:
                        logger.info(f"Job {job_id}: Processed {stats['processed_rows']}/{total_rows} rows "
                                  f"({stats['processed_rows']/total_rows*100:.1f}%)")

                except Exception as e:
                    error_msg = f"Failed to process parquet batch {batch_number}: {e}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

        stats["duration"] = time.time() - start_time
        mark_job_completed(
            job_id,
            records_processed=stats["processed_rows"],
            sentiment_records=stats["sentiment_records"],
            entity_records=stats["entity_records"],
            duration=stats["duration"],
            errors=stats["errors"],
        )
        logger.info(f"Parquet job {job_id} completed in {stats['duration']:.2f}s.")
        return stats

    except Exception as exc:
        stats["duration"] = time.time() - start_time
        mark_job_failed(
            job_id,
            str(exc),
            records_processed=stats["processed_rows"],
            sentiment_records=stats["sentiment_records"],
            entity_records=stats["entity_records"],
            duration=stats["duration"],
        )
        logger.error(f"Parquet job {job_id} failed: {exc}", exc_info=True)
        raise
