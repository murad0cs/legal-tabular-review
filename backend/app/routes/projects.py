from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import ProjectService, ExtractionService, ValidationService
from ..schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    AddDocumentsRequest, ExtractedValueResponse,
    ExtractedValueUpdate, ExtractedValuesResponse, BulkValueActionRequest,
    BulkValueActionResponse
)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
def list_projects(db: Session = Depends(get_db)):
    service = ProjectService(db)
    projects = service.get_all()
    return ProjectListResponse(projects=[
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            template_id=p.template_id,
            created_at=p.created_at,
            updated_at=p.updated_at,
            status=p.status,
            document_count=p.document_count
        ) for p in projects
    ])


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.get_by_id(project_id)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "template_id": project.template_id,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "status": project.status,
        "document_count": project.document_count,
        "documents": [
            {
                "id": pd.document.id,
                "original_filename": pd.document.original_filename,
                "file_type": pd.document.file_type,
                "page_count": pd.document.page_count,
                "status": pd.document.status,
                "upload_date": pd.document.upload_date.isoformat()
            } for pd in project.project_documents
        ],
        "template": {
            "id": project.template.id,
            "name": project.template.name,
            "description": project.template.description,
            "document_type": project.template.document_type,
            "fields": [
                {
                    "id": f.id,
                    "field_name": f.field_name,
                    "field_label": f.field_label,
                    "field_type": f.field_type,
                    "is_required": f.is_required
                } for f in project.template.fields
            ]
        } if project.template else None
    }


@router.post("", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.create(name=data.name, template_id=data.template_id, description=data.description)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        template_id=project.template_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        status=project.status,
        document_count=project.document_count
    )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.update(project_id, **data.model_dump(exclude_unset=True))
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        template_id=project.template_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        status=project.status,
        document_count=project.document_count
    )


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    service = ProjectService(db)
    service.delete(project_id)
    return {"message": "Project deleted"}


@router.post("/{project_id}/documents")
def add_documents(project_id: int, data: AddDocumentsRequest, db: Session = Depends(get_db)):
    service = ProjectService(db)
    added = service.add_documents(project_id, data.document_ids)
    return {"message": f"Added {len(added)} documents", "document_ids": [pd.document_id for pd in added]}


@router.delete("/{project_id}/documents/{document_id}")
def remove_document(project_id: int, document_id: int, db: Session = Depends(get_db)):
    service = ProjectService(db)
    service.remove_document(project_id, document_id)
    return {"message": "Document removed"}


@router.post("/{project_id}/extract")
def extract_fields(project_id: int, db: Session = Depends(get_db)):
    service = ExtractionService(db)
    values = service.extract_for_project(project_id)
    return {"message": f"Extracted {len(values)} values", "count": len(values)}


@router.get("/{project_id}/values", response_model=ExtractedValuesResponse)
def get_values(project_id: int, db: Session = Depends(get_db)):
    service = ExtractionService(db)
    validation_service = ValidationService(db)
    values = service.get_project_values(project_id)
    
    # Get validation summary
    validation_summary = validation_service.get_validation_summary(project_id)
    
    return ExtractedValuesResponse(
        values=[
            ExtractedValueResponse(
                id=v.id,
                document_id=v.document_id,
                template_field_id=v.template_field_id,
                project_id=v.project_id,
                field_name=v.field_name,
                field_label=v.field_label,
                raw_value=v.raw_value,
                normalized_value=v.normalized_value,
                confidence=v.confidence,
                citation=v.citation,
                citation_text=v.citation_text,
                status=v.status,
                reviewed_by=v.reviewed_by,
                reviewed_at=v.reviewed_at,
                validation_errors=v.validation_errors,
                created_at=v.created_at,
                updated_at=v.updated_at
            ) for v in values
        ],
        validation_summary={"valid": validation_summary["valid"], "invalid": validation_summary["invalid"]}
    )


@router.post("/values/bulk/approve", response_model=BulkValueActionResponse)
def bulk_approve_values(data: BulkValueActionRequest, db: Session = Depends(get_db)):
    """Approve multiple values at once."""
    service = ExtractionService(db)
    updated_ids = service.bulk_approve(data.value_ids)
    return BulkValueActionResponse(
        message=f"Approved {len(updated_ids)} values",
        count=len(updated_ids),
        updated_ids=updated_ids
    )


@router.post("/values/bulk/reject", response_model=BulkValueActionResponse)
def bulk_reject_values(data: BulkValueActionRequest, db: Session = Depends(get_db)):
    """Reject multiple values at once."""
    service = ExtractionService(db)
    updated_ids = service.bulk_reject(data.value_ids)
    return BulkValueActionResponse(
        message=f"Rejected {len(updated_ids)} values",
        count=len(updated_ids),
        updated_ids=updated_ids
    )


@router.put("/values/{value_id}", response_model=ExtractedValueResponse)
def update_value(value_id: int, data: ExtractedValueUpdate, db: Session = Depends(get_db)):
    service = ExtractionService(db)
    value = service.update_value(value_id, new_value=data.raw_value, status=data.status, reviewer=data.reviewer)
    return ExtractedValueResponse(
        id=value.id,
        document_id=value.document_id,
        template_field_id=value.template_field_id,
        project_id=value.project_id,
        field_name=value.field_name,
        field_label=value.field_label,
        raw_value=value.raw_value,
        normalized_value=value.normalized_value,
        confidence=value.confidence,
        citation=value.citation,
        citation_text=value.citation_text,
        status=value.status,
        reviewed_by=value.reviewed_by,
        reviewed_at=value.reviewed_at,
        created_at=value.created_at,
        updated_at=value.updated_at
    )


@router.post("/values/{value_id}/approve", response_model=ExtractedValueResponse)
def approve_value(value_id: int, db: Session = Depends(get_db)):
    service = ExtractionService(db)
    value = service.approve_value(value_id)
    return ExtractedValueResponse(
        id=value.id,
        document_id=value.document_id,
        template_field_id=value.template_field_id,
        project_id=value.project_id,
        field_name=value.field_name,
        field_label=value.field_label,
        raw_value=value.raw_value,
        normalized_value=value.normalized_value,
        confidence=value.confidence,
        citation=value.citation,
        citation_text=value.citation_text,
        status=value.status,
        reviewed_by=value.reviewed_by,
        reviewed_at=value.reviewed_at,
        created_at=value.created_at,
        updated_at=value.updated_at
    )


@router.post("/values/{value_id}/reject", response_model=ExtractedValueResponse)
def reject_value(value_id: int, db: Session = Depends(get_db)):
    service = ExtractionService(db)
    value = service.reject_value(value_id)
    return ExtractedValueResponse(
        id=value.id,
        document_id=value.document_id,
        template_field_id=value.template_field_id,
        project_id=value.project_id,
        field_name=value.field_name,
        field_label=value.field_label,
        raw_value=value.raw_value,
        normalized_value=value.normalized_value,
        confidence=value.confidence,
        citation=value.citation,
        citation_text=value.citation_text,
        status=value.status,
        reviewed_by=value.reviewed_by,
        reviewed_at=value.reviewed_at,
        created_at=value.created_at,
        updated_at=value.updated_at
    )


@router.post("/{project_id}/re-extract")
def re_extract_fields(project_id: int, db: Session = Depends(get_db)):
    """Re-extract all fields for a project. Use when template has been updated."""
    extraction_service = ExtractionService(db)
    validation_service = ValidationService(db)
    
    # Run extraction
    values = extraction_service.extract_for_project(project_id)
    
    # Run validation on newly extracted values
    validation_result = validation_service.validate_project_values(project_id)
    
    return {
        "message": f"Re-extracted {len(values)} values",
        "extraction_count": len(values),
        "validation": validation_result
    }
