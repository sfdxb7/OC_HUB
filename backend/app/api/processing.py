"""
Processing API endpoints - document upload and processing pipeline.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.core.deps import get_admin_user
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# === Request/Response Models ===

class ProcessingJob(BaseModel):
    """Processing job status."""
    id: UUID
    type: str  # 'bulk_upload', 'single_reprocess'
    status: str  # 'pending', 'running', 'completed', 'failed'
    total_items: int
    processed_items: int
    failed_items: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


class ProcessingItem(BaseModel):
    """Individual item in processing job."""
    filename: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    error: Optional[str]
    report_id: Optional[UUID]


class ProcessingDetail(BaseModel):
    """Detailed processing job info."""
    id: UUID
    type: str
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    items: list[ProcessingItem]
    created_by: UUID
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]


# === Endpoints ===

@router.post("/upload", response_model=ProcessingJob)
async def upload_reports(
    file: UploadFile = File(..., description="ZIP file containing MinerU outputs"),
    current_user: dict = Depends(get_admin_user)
):
    """
    Upload ZIP of MinerU-processed reports for ingestion.
    
    Expected ZIP structure:
    ```
    reports.zip
    ├── Report_Name_1/
    │   └── vlm/
    │       ├── Report_Name_1.md
    │       ├── Report_Name_1_content_list.json
    │       └── images/
    ├── Report_Name_2/
    │   └── vlm/
    │       └── ...
    └── ...
    ```
    
    Processing pipeline:
    1. Validate ZIP structure
    2. Parse MinerU outputs
    3. Upload to RAGFlow (with GraphRAG)
    4. Run intelligence extraction (Grok Fast)
    5. Store in Supabase
    
    Returns job ID for status tracking.
    """
    logger.info(
        "Upload reports",
        user_id=current_user["id"],
        filename=file.filename,
        content_type=file.content_type
    )
    
    # Validate file type
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive"
        )
    
    # TODO: Implement upload processing
    # 1. Save ZIP to temp location
    # 2. Create processing job in Supabase
    # 3. Start background task
    # 4. Return job ID
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Upload not yet implemented"
    )


@router.get("/processing", response_model=list[ProcessingJob])
async def list_processing_jobs(
    current_user: dict = Depends(get_admin_user),
    status_filter: Optional[str] = None,
    limit: int = 20
):
    """
    List all processing jobs.
    """
    logger.info(
        "List processing jobs",
        user_id=current_user["id"]
    )
    
    # TODO: Query Supabase for processing jobs
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List processing jobs not yet implemented"
    )


@router.get("/processing/{job_id}", response_model=ProcessingDetail)
async def get_processing_status(
    job_id: UUID,
    current_user: dict = Depends(get_admin_user)
):
    """
    Get detailed status of a processing job.
    
    Includes status of individual items.
    """
    logger.info(
        "Get processing status",
        user_id=current_user["id"],
        job_id=str(job_id)
    )
    
    # TODO: Query Supabase for job details
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get processing status not yet implemented"
    )


@router.post("/reprocess/{report_id}", response_model=ProcessingJob)
async def reprocess_report(
    report_id: UUID,
    current_user: dict = Depends(get_admin_user)
):
    """
    Reprocess a specific report.
    
    Useful if extraction failed or you want to use updated prompts.
    """
    logger.info(
        "Reprocess report",
        user_id=current_user["id"],
        report_id=str(report_id)
    )
    
    # TODO: Trigger reprocessing
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Reprocess not yet implemented"
    )


@router.delete("/processing/{job_id}")
async def cancel_processing_job(
    job_id: UUID,
    current_user: dict = Depends(get_admin_user)
):
    """
    Cancel a running processing job.
    """
    logger.info(
        "Cancel processing job",
        user_id=current_user["id"],
        job_id=str(job_id)
    )
    
    # TODO: Cancel job if still running
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Cancel processing not yet implemented"
    )
