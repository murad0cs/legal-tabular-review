from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    page_count = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="uploaded")
    error_message = Column(Text, nullable=True)
    
    extracted_values = relationship(
        "ExtractedValue",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    project_documents = relationship(
        "ProjectDocument",
        back_populates="document",
        cascade="all, delete-orphan"
    )
