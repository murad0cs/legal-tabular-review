from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.validation_service import ValidationService

router = APIRouter(prefix="/api/validation", tags=["Validation"])


@router.post("/projects/{project_id}/validate")
def validate_project(project_id: int, db: Session = Depends(get_db)):
    """Validate all extracted values in a project against their field rules."""
    service = ValidationService(db)
    result = service.validate_project_values(project_id)
    return result


@router.get("/projects/{project_id}/summary")
def get_validation_summary(project_id: int, db: Session = Depends(get_db)):
    """Get validation summary for a project."""
    service = ValidationService(db)
    return service.get_validation_summary(project_id)

