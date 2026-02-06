from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services import DocumentService
from ..schemas import DocumentResponse, DocumentListResponse, DocumentContentResponse
from ..config import get_settings

router = APIRouter(prefix="/api/documents", tags=["Documents"])
settings = get_settings()


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)):
    service = DocumentService(db)
    documents = service.get_all()
    return DocumentListResponse(documents=[DocumentResponse.model_validate(d) for d in documents])


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    service = DocumentService(db)
    document = service.get_by_id(document_id)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/content", response_model=DocumentContentResponse)
def get_document_content(document_id: int, db: Session = Depends(get_db)):
    service = DocumentService(db)
    document = service.get_by_id(document_id)
    return DocumentContentResponse(id=document.id, filename=document.original_filename, content=document.content)


@router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    service = DocumentService(db)
    uploaded = []
    errors = []
    
    for file in files:
        ext = file.filename.split(".")[-1].lower()
        if ext not in settings.allowed_extensions:
            errors.append({"filename": file.filename, "error": f"File type '{ext}' not allowed"})
            continue
        
        content = await file.read()
        if len(content) > settings.max_file_size_bytes:
            errors.append({"filename": file.filename, "error": f"File exceeds {settings.max_file_size_mb}MB limit"})
            continue
        
        await file.seek(0)
        
        try:
            document = await service.upload(file)
            uploaded.append(DocumentResponse.model_validate(document))
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
    
    return {"uploaded": uploaded, "errors": errors}


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    service = DocumentService(db)
    service.delete(document_id)
    return {"message": "Document deleted"}
