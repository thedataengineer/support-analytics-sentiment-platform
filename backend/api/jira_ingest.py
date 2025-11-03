import os
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..jobs.ingest_job import process_parquet_job
from ..jobs.job_status import init_job

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_PARQUET_PATH = os.getenv(
    "JIRA_PARQUET_PATH", "/Users/karteek/dev/work/accionlabs/jira-profiler/Jira.parquet"
)


@router.post("/ingest-jira")
async def ingest_jira_parquet(parquet_path: Optional[str] = Query(None, description="Path to Jira parquet export")):
    """
    Schedule parquet ingestion for the Jira profiler export.
    """
    source_path = parquet_path or DEFAULT_PARQUET_PATH

    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail=f"Parquet file not found at {source_path}")

    try:
        import pyarrow.parquet as pq

        parquet_file = pq.ParquetFile(source_path)
        metadata = {
            "total_rows": parquet_file.metadata.num_rows,
            "total_columns": parquet_file.metadata.num_columns,
        }
    except Exception as exc:
        logger.error(f"Failed to open parquet file {source_path}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to inspect parquet file: {exc}")

    job_id = f"jira-{uuid.uuid4()}"
    init_job(
        job_id,
        source="parquet",
        file_name=os.path.basename(source_path),
        metadata=metadata | {"parquet_path": source_path},
    )

    process_parquet_job.delay(job_id, source_path)
    logger.info(f"Scheduled parquet ingestion job {job_id} for {source_path}")

    return {
        "job_id": job_id,
        "status_url": f"/api/job/{job_id}",
        "message": "Parquet ingestion scheduled",
        "metadata": metadata,
    }
