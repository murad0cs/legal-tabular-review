"""
Evaluation API Routes

Provides endpoints for quality evaluation of extraction results.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict

from ..database import get_db
from ..services.evaluation_service import EvaluationService
from ..exceptions import NotFoundError

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


class EvaluationRequest(BaseModel):
    """Request body for evaluation."""
    ground_truth: Dict[str, Dict[str, str]]  # {doc_name: {field_name: expected_value}}


@router.post("/projects/{project_id}/evaluate")
def evaluate_project(
    project_id: int,
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate extraction results against ground truth.
    
    Compare AI-extracted values with human-labeled reference data.
    Returns precision, recall, F1 score, and per-field accuracy.
    """
    try:
        service = EvaluationService(db)
        result = service.evaluate_project(project_id, request.ground_truth)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/projects/{project_id}/summary")
def get_evaluation_summary(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get quick quality summary for a project.
    
    Returns confidence distribution, quality score, and rating.
    """
    try:
        service = EvaluationService(db)
        return service.get_evaluation_summary(project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

