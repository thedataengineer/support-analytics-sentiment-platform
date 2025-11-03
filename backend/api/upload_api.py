from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
from pathlib import Path

from config import settings
from services.upload_service import upload_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/file")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accept a file upload and persist it locally for later processing.
    """
    logger.info("Receiving file upload: %s (%s)", file.filename, file.content_type)

    try:
        content = await file.read()
        size = len(content)
        if size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        if size > settings.max_upload_size:
            raise HTTPException(status_code=413, detail="Uploaded file exceeds size limit")

        extension = Path(file.filename).suffix.lower()
        if extension not in settings.allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file extension: {extension}")

        metadata = upload_service.save_file(content, file.filename)
        return JSONResponse(
            {
                "status": "success",
                "file": metadata,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to store uploaded file %s: %s", file.filename, exc)
        raise HTTPException(status_code=500, detail="Failed to store uploaded file") from exc


@router.get("/file-metadata")
async def file_metadata(path: str = Query(..., description="Absolute path to stored file")) -> Dict[str, Any]:
    """
    Return metadata for a stored upload.
    """
    metadata = upload_service.get_file_metadata(path)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")

    return JSONResponse({"status": "success", "metadata": metadata})


@router.delete("/file")
async def delete_file(path: str = Query(..., description="Absolute path to stored file")) -> Dict[str, Any]:
    """
    Delete a stored upload.
    """
    if not upload_service.delete_file(path):
        raise HTTPException(status_code=404, detail="File not found")

    return JSONResponse({"status": "success"})
