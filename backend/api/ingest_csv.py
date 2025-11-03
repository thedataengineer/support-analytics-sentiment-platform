from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import os
import uuid
import logging
from typing import Dict, Any, Optional, List

from jobs.parquet_ingest_job import process_csv_content_parquet_task, process_json_ingest_parquet_task
from jobs.celery_config import celery_app
from jobs.job_status import (
    init_job,
    get_job,
    list_jobs,
    mark_job_failed,
)
from config import settings
from .auth import require_role

logger = logging.getLogger(__name__)


# Pydantic models for JSON ingest
class IngestRecord(BaseModel):
    """Single record for JSON ingestion"""
    id: str = Field(..., max_length=100, description="Unique record ID")
    summary: Optional[str] = Field(None, description="Record summary")
    description: Optional[str] = Field(None, description="Record description")
    comments: Optional[List[str]] = Field(None, description="List of comments")

    @field_validator('summary', 'description')
    @classmethod
    def at_least_one_text_field(cls, v, info):
        # Validate that at least summary or description is provided
        if not v and not info.data.get('description') and not info.data.get('summary'):
            raise ValueError("At least one of 'summary' or 'description' must be provided")
        return v


class IngestRequest(BaseModel):
    """Request payload for batch JSON ingestion"""
    records: List[IngestRecord] = Field(..., min_length=1, max_length=1000)

    @field_validator('records')
    @classmethod
    def validate_record_count(cls, v):
        if len(v) == 0:
            raise ValueError("records cannot be empty")
        if len(v) > 1000:
            raise ValueError("records exceeds batch limit of 1000")
        return v


def validate_csv_content(file_path: str) -> Dict[str, Any]:
    """
    Validate CSV file content and structure
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary with validation results
        
    Raises:
        Exception: If validation fails
    """
    try:
        # Try to read with different encodings if needed
        df = None
        encodings_to_try = ['utf-8', 'latin1', 'cp1252']

        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(file_path, nrows=10, encoding=encoding)  # Read first 10 rows for validation
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            raise Exception("Unable to decode CSV file with supported encodings")

        if df.empty:
            raise Exception("CSV file is empty")

        # Basic validation - check for text columns
        text_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in
                        ['text', 'description', 'summary', 'comment', 'feedback', 'message', 'content'])]

        if not text_columns:
            raise Exception(f"No text columns found in CSV. Columns: {list(df.columns)}")

        return {
            "valid": True,
            "rows": len(df),
            "columns": len(df.columns),
            "text_columns": text_columns
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Upload and process a CSV file for sentiment analysis
    """
    logger.info(f"Received file upload: {file.filename}")

    # Validate file extension
    if not file.filename or not file.filename.lower().endswith('.csv'):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="File must be a CSV with .csv extension")

    # Validate file size
    file_size = 0
    content_chunks = []
    try:
        while chunk := await file.read(8192):  # Read in 8KB chunks
            file_size += len(chunk)
            if file_size > settings.max_upload_size:
                logger.warning(f"File too large: {file_size} bytes")
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds maximum allowed size of {settings.max_upload_size} bytes"
                )
            content_chunks.append(chunk)
    except Exception as e:
        logger.error(f"Error reading file content: {e}")
        raise HTTPException(status_code=400, detail="Failed to read file content")

    # Store file content in memory for processing
    file_content = b''.join(content_chunks)
    logger.info(f"File loaded into memory: {file.filename} ({file_size} bytes)")

    # Validate CSV structure
    try:
        import io
        # Try to read with different encodings if needed
        df = None
        encodings_to_try = ['utf-8', 'latin1', 'cp1252']

        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(io.BytesIO(file_content), nrows=10, encoding=encoding)  # Read first 10 rows for validation
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            raise Exception("Unable to decode CSV file with supported encodings")

        if df.empty:
            logger.warning("Uploaded CSV file is empty")
            raise HTTPException(status_code=400, detail="CSV file is empty")

        # Basic validation - check for text columns
        text_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in
                        ['text', 'description', 'summary', 'comment', 'feedback', 'message', 'content'])]

        if not text_columns:
            logger.warning(f"No text columns found in CSV. Columns: {list(df.columns)}")
            raise HTTPException(
                status_code=400,
                detail="No text columns found in CSV. Expected columns containing 'text', 'description', 'summary', 'comment', 'feedback', 'message', or 'content'"
            )

        logger.info(f"CSV validation successful. Found {len(df)} rows and {len(df.columns)} columns. Text columns: {text_columns}")

    except pd.errors.EmptyDataError:
        logger.warning("CSV file appears to be empty or malformed")
        raise HTTPException(status_code=400, detail="CSV file is empty or malformed")
    except pd.errors.ParserError as e:
        logger.warning(f"CSV parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during CSV validation: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

    # Generate job ID and trigger async processing
    job_id = str(uuid.uuid4())
    logger.info(f"Created job {job_id} for file processing")

    init_job(
        job_id,
        source="csv_upload",
        file_name=file.filename,
        metadata={
            "file_size": file_size,
            "total_columns": len(df.columns),
            "detected_text_columns": text_columns,
        },
    )

    try:
        # Process using new Parquet pipeline
        celery_app.send_task(
            "backend.jobs.parquet_ingest_job.process_csv_content_parquet_task",
            args=[file_content.decode('utf-8'), job_id, file.filename]
        )

        logger.info(f"Successfully queued Parquet job {job_id} for async processing")
        return JSONResponse({
            "job_id": job_id,
            "status_url": f"/api/job/{job_id}",
            "message": "Upload successful, processing started",
            "file_info": {
                "filename": file.filename,
                "size": file_size,
                "rows": len(df),
                "columns": len(df.columns),
                "text_columns": text_columns
            }
        })

    except Exception as e:
        logger.error(f"Failed to queue job {job_id}: {e}")
        mark_job_failed(job_id, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to queue processing: {str(e)}")

@router.post("/data-ingest", dependencies=[Depends(require_role("analyst", "admin"))])
async def ingest_data(payload: IngestRequest):
    """
    API endpoint for batch JSON data ingestion.

    Requires authentication with analyst or admin role.

    Args:
        payload: IngestRequest containing list of records to ingest

    Returns:
        Job ID and status URL for tracking progress
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Received JSON ingest request with {len(payload.records)} records, job_id={job_id}")

    # Initialize job tracking
    init_job(
        job_id,
        source="json_api",
        file_name=f"{len(payload.records)}-records.json",
        metadata={
            "total_records": len(payload.records),
        }
    )

    try:
        # Convert Pydantic models to dicts for Celery serialization
        records_data = [record.model_dump() for record in payload.records]

        # Dispatch async Celery task using Parquet pipeline
        celery_app.send_task(
            "backend.jobs.parquet_ingest_job.process_json_ingest_parquet_task",
            args=[job_id, records_data]
        )

        logger.info(f"Successfully queued JSON ingestion job {job_id}")
        return JSONResponse({
            "job_id": job_id,
            "status_url": f"/api/job/{job_id}",
            "message": "Data ingestion started",
            "record_count": len(payload.records)
        })

    except Exception as e:
        logger.error(f"Failed to queue JSON ingestion job {job_id}: {e}")
        mark_job_failed(job_id, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to queue ingestion: {str(e)}")

@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    # Simplified job status - in production, check from database/cache
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse(job)

@router.get("/jobs")
async def list_job_statuses(
    status: Optional[str] = Query(None, description="Filter by job status"),
    limit: int = Query(20, le=100, description="Max number of jobs to return")
):
    jobs = list_jobs(status=status, limit=limit)
    return JSONResponse({
        "results": jobs,
        "count": len(jobs)
    })
