from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..services.search_service import SearchService

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("")
def search_values(
    q: str = Query(..., min_length=1, description="Search query"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    field_type: Optional[str] = Query(None, description="Filter by field type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence"),
    max_confidence: Optional[float] = Query(None, ge=0, le=1, description="Maximum confidence"),
    limit: int = Query(50, ge=1, le=200, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """Search across all extracted values.
    
    Searches in: raw_value, normalized_value, citation_text, field labels, document names
    """
    service = SearchService(db)
    return service.search(
        query=q,
        project_id=project_id,
        field_type=field_type,
        status=status,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        limit=limit,
        offset=offset
    )


@router.get("/field-types")
def get_field_types(db: Session = Depends(get_db)):
    """Get all available field types for filtering."""
    service = SearchService(db)
    return {"field_types": service.get_field_types()}


@router.get("/suggestions")
def get_suggestions(
    q: str = Query(..., min_length=2, description="Partial search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on existing values."""
    service = SearchService(db)
    return {"suggestions": service.get_search_suggestions(q, limit)}

