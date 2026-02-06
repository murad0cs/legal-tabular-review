from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_type: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    page_count: int
    upload_date: datetime
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DocumentContentResponse(BaseModel):
    id: int
    filename: str
    content: Optional[str] = None

