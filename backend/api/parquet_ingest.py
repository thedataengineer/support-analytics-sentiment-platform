from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import uuid
import logging
import os
from typing import Dict, Any

from jobs.parquet_ingest_job import process_csv_content_parquet_task
from jobs.celery_config import celery_app
from jobs.job_status import init_job, mark_job_failed
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-parquet")
async def upload_parquet(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload and process a Parquet file"""

    if not file.filename or not file.filename.lower().endswith('.parquet'):
        raise HTTPException(status_code=400, detail="File must be a Parquet file")

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

    # Combine chunks into bytes
    content = b''.join(content_chunks)
    logger.info(f"File loaded into memory: {file.filename} ({file_size} bytes)")

    # Generate job ID
    job_id = str(uuid.uuid4())

    init_job(
        job_id,
        source="parquet_upload",
        file_name=file.filename,
        metadata={"file_size": file_size}
    )

    try:
        # Validate Parquet structure by reading metadata
        import io
        import pyarrow.parquet as pq

        # Read parquet metadata without full file load
        parquet_file = pq.ParquetFile(io.BytesIO(content))
        metadata = parquet_file.metadata

        # Get schema information safely
        schema_info = []
        try:
            for i in range(metadata.num_columns):
                col_name = metadata.schema.names[i]
                col_type = str(metadata.schema.types[i])
                schema_info.append({"name": col_name, "type": col_type})
        except Exception as e:
            logger.warning(f"Could not extract schema info: {e}")
            schema_info = [{"name": f"column_{i}", "type": "unknown"} for i in range(metadata.num_columns)]

        file_info = {
            "filename": file.filename,
            "size": file_size,
            "rows": metadata.num_rows,
            "columns": metadata.num_columns,
            "schema": schema_info
        }

        logger.info(f"Parquet validation successful. Found {metadata.num_rows} rows and {metadata.num_columns} columns.")

        # Convert Parquet to CSV for processing (temporary solution)
        import io
        df = pd.read_parquet(io.BytesIO(content))
        csv_content = df.to_csv(index=False)
        
        # Queue async processing task using CSV pipeline
        celery_app.send_task(
            "backend.jobs.parquet_ingest_job.process_csv_content_parquet_task",
            args=[csv_content, job_id, file.filename]
        )

        logger.info(f"Successfully queued parquet processing job {job_id}")

        return JSONResponse({
            "job_id": job_id,
            "status_url": f"/api/job/{job_id}",
            "message": "Parquet upload successful, processing started",
            "file_info": file_info
        })

    except Exception as e:
        logger.error(f"Failed to process parquet upload: {e}")
        mark_job_failed(job_id, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process parquet: {str(e)}")