"""Base repository implementing generic CRUD operations."""
from typing import TypeVar, Generic, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository with common CRUD operations."""
    
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get a single entity by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, **filters) -> list[T]:
        """Get all entities with optional filtering and pagination."""
        query = self.db.query(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, **filters) -> int:
        """Count entities with optional filtering."""
        query = self.db.query(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def create(self, entity: T) -> T:
        """Create a new entity."""
        self.db.add(entity)
        self.db.flush()
        return entity
    
    def create_many(self, entities: list[T]) -> list[T]:
        """Create multiple entities."""
        self.db.add_all(entities)
        self.db.flush()
        return entities
    
    def update(self, id: int, data: dict) -> Optional[T]:
        """Update an entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return None
        
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        self.db.flush()
        return entity
    
    def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return False
        
        self.db.delete(entity)
        self.db.flush()
        return True
    
    def delete_many(self, ids: list[int]) -> int:
        """Delete multiple entities by IDs."""
        deleted = self.db.query(self.model).filter(
            self.model.id.in_(ids)
        ).delete(synchronize_session=False)
        self.db.flush()
        return deleted
    
    def exists(self, id: int) -> bool:
        """Check if an entity exists."""
        return self.db.query(
            self.db.query(self.model).filter(self.model.id == id).exists()
        ).scalar()
    
    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()
    
    def refresh(self, entity: T) -> T:
        """Refresh an entity from the database."""
        self.db.refresh(entity)
        return entity


