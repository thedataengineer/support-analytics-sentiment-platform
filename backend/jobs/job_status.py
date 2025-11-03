"""
Shared helpers for tracking ingestion job status in Redis (with in-memory fallback).
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Dict, List, Optional, Any

from cache import cache

JOB_KEY_PREFIX = "ingest_job"
JOB_INDEX_KEY = "ingest_job:index"
JOB_TTL_SECONDS = 7 * 24 * 60 * 60  # keep jobs for 7 days

_local_store: Dict[str, Dict[str, Any]] = {}
_local_index: List[str] = []


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _job_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}:{job_id}"


def _save_job(job_id: str, data: Dict[str, Any]) -> None:
    data.setdefault("updated_at", _now_iso())
    if cache.redis_client:
        cache.redis_client.setex(_job_key(job_id), JOB_TTL_SECONDS, json.dumps(data))
        cache.redis_client.zadd(JOB_INDEX_KEY, {job_id: datetime.now(tz=timezone.utc).timestamp()})
    else:
        _local_store[job_id] = data
        if job_id not in _local_index:
            _local_index.append(job_id)


def _get_job(job_id: str) -> Optional[Dict[str, Any]]:
    if cache.redis_client:
        raw = cache.redis_client.get(_job_key(job_id))
        if raw:
            try:
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, TypeError):
                return None
        return None
    return _local_store.get(job_id)


def _update_job(job_id: str, **updates: Any) -> Dict[str, Any]:
    job = _get_job(job_id) or {}
    job.setdefault("job_id", job_id)
    for key, value in updates.items():
        job[key] = value
    job["updated_at"] = _now_iso()
    _save_job(job_id, job)
    return job


def init_job(job_id: str, *, source: str, file_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "job_id": job_id,
        "source": source,
        "file_name": file_name,
        "status": "queued",
        "submitted_at": _now_iso(),
        "started_at": None,
        "completed_at": None,
        "records_processed": 0,
        "sentiment_records": 0,
        "entity_records": 0,
        "error": None,
    }
    if metadata:
        payload.update(metadata)
    _save_job(job_id, payload)
    return payload


def mark_job_running(job_id: str, **metadata: Any) -> Dict[str, Any]:
    updates = {"status": "running"}
    if metadata:
        updates.update(metadata)
    updates.setdefault("started_at", _now_iso())
    return _update_job(job_id, **updates)


def increment_job_progress(job_id: str, *, processed: int = 0, sentiment_records: int = 0, entity_records: int = 0) -> Dict[str, Any]:
    job = _get_job(job_id) or {}
    new_totals = {
        "records_processed": job.get("records_processed", 0) + processed,
        "sentiment_records": job.get("sentiment_records", 0) + sentiment_records,
        "entity_records": job.get("entity_records", 0) + entity_records,
    }
    return _update_job(job_id, **new_totals)


def update_job_metadata(job_id: str, **metadata: Any) -> Dict[str, Any]:
    return _update_job(job_id, **metadata)


def mark_job_completed(job_id: str, **metadata: Any) -> Dict[str, Any]:
    updates = {"status": "completed", "completed_at": _now_iso()}
    if metadata:
        updates.update(metadata)
    return _update_job(job_id, **updates)


def mark_job_failed(job_id: str, error: str, **metadata: Any) -> Dict[str, Any]:
    updates = {"status": "failed", "error": error, "completed_at": _now_iso()}
    if metadata:
        updates.update(metadata)
    return _update_job(job_id, **updates)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _get_job(job_id)


def list_jobs(*, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if cache.redis_client:
        job_ids = cache.redis_client.zrevrange(JOB_INDEX_KEY, 0, limit - 1)
        for raw_id in job_ids:
            job_id = raw_id.decode()
            job = _get_job(job_id)
            if not job:
                continue
            if status and job.get("status") != status:
                continue
            results.append(job)
            if len(results) >= limit:
                break
    else:
        for job_id in reversed(_local_index):
            job = _local_store.get(job_id)
            if not job:
                continue
            if status and job.get("status") != status:
                continue
            results.append(job)
            if len(results) >= limit:
                break
    return results
