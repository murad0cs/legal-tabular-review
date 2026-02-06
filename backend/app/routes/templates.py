from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import TemplateService
from ..schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse,
    FieldCreate, FieldUpdate, FieldResponse, FieldReorderRequest, TemplateExport
)

router = APIRouter(prefix="/api/templates", tags=["Templates"])


@router.get("", response_model=TemplateListResponse)
def list_templates(db: Session = Depends(get_db)):
    service = TemplateService(db)
    templates = service.get_all()
    return TemplateListResponse(templates=[TemplateResponse.model_validate(t) for t in templates])


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    service = TemplateService(db)
    template = service.get_by_id(template_id)
    return TemplateResponse.model_validate(template)


@router.post("", response_model=TemplateResponse)
def create_template(data: TemplateCreate, db: Session = Depends(get_db)):
    service = TemplateService(db)
    template = service.create(name=data.name, document_type=data.document_type, description=data.description)
    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(template_id: int, data: TemplateUpdate, db: Session = Depends(get_db)):
    service = TemplateService(db)
    template = service.update(template_id, name=data.name, description=data.description, document_type=data.document_type)
    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    service = TemplateService(db)
    service.delete(template_id)
    return {"message": "Template deleted"}


@router.post("/{template_id}/fields", response_model=FieldResponse)
def add_field(template_id: int, data: FieldCreate, db: Session = Depends(get_db)):
    service = TemplateService(db)
    field = service.add_field(
        template_id=template_id,
        field_name=data.field_name,
        field_label=data.field_label,
        field_type=data.field_type,
        description=data.description,
        normalization_rule=data.normalization_rule,
        is_required=data.is_required,
        validation_rules=data.validation_rules
    )
    return FieldResponse.model_validate(field)


@router.put("/{template_id}/fields/{field_id}", response_model=FieldResponse)
def update_field(template_id: int, field_id: int, data: FieldUpdate, db: Session = Depends(get_db)):
    service = TemplateService(db)
    field = service.update_field(field_id, **data.model_dump(exclude_unset=True))
    return FieldResponse.model_validate(field)


@router.delete("/{template_id}/fields/{field_id}")
def delete_field(template_id: int, field_id: int, db: Session = Depends(get_db)):
    service = TemplateService(db)
    service.delete_field(field_id)
    return {"message": "Field deleted"}


@router.post("/{template_id}/fields/reorder")
def reorder_fields(template_id: int, data: FieldReorderRequest, db: Session = Depends(get_db)):
    service = TemplateService(db)
    service.reorder_fields(template_id, data.field_ids)
    return {"message": "Fields reordered"}


@router.get("/{template_id}/export")
def export_template(template_id: int, db: Session = Depends(get_db)):
    """Export a template as JSON for sharing or backup."""
    service = TemplateService(db)
    template = service.get_by_id(template_id)
    
    export_data = {
        "name": template.name,
        "description": template.description,
        "document_type": template.document_type,
        "fields": [
            {
                "field_name": f.field_name,
                "field_label": f.field_label,
                "field_type": f.field_type,
                "description": f.description,
                "normalization_rule": f.normalization_rule,
                "is_required": f.is_required,
                "validation_rules": f.validation_rules
            }
            for f in template.fields
        ]
    }
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="{template.name.replace(" ", "_")}_template.json"'
        }
    )


@router.post("/import", response_model=TemplateResponse)
def import_template(data: TemplateExport, db: Session = Depends(get_db)):
    """Import a template from JSON."""
    service = TemplateService(db)
    
    # Create the template
    template = service.create(
        name=data.name,
        document_type=data.document_type,
        description=data.description
    )
    
    # Add all fields
    for field_data in data.fields:
        service.add_field(
            template_id=template.id,
            field_name=field_data.field_name,
            field_label=field_data.field_label,
            field_type=field_data.field_type,
            description=field_data.description,
            normalization_rule=field_data.normalization_rule,
            is_required=field_data.is_required,
            validation_rules=field_data.validation_rules
        )
    
    # Refresh to get all fields
    template = service.get_by_id(template.id)
    return TemplateResponse.model_validate(template)
