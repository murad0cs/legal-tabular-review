from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ..models.comment import Comment
from ..models.extracted_value import ExtractedValue
from .audit_service import AuditService


class CommentService:
    """Service for managing comments on extracted values."""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
    
    def create_comment(
        self,
        value_id: int,
        content: str,
        author: str = "user"
    ) -> Comment:
        """Add a comment to an extracted value."""
        # Verify the value exists and get project context
        value = self.db.query(ExtractedValue).filter(ExtractedValue.id == value_id).first()
        if not value:
            raise ValueError(f"Extracted value {value_id} not found")
        
        comment = Comment(
            extracted_value_id=value_id,
            content=content,
            author=author,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        # Log the comment creation
        self.audit_service.log_comment(
            value_id=value_id,
            comment_id=comment.id,
            action="comment_added",
            user=author,
            content=content,
            project_id=value.project_id
        )
        
        return comment
    
    def update_comment(
        self,
        comment_id: int,
        content: str,
        author: str = "user"
    ) -> Optional[Comment]:
        """Update an existing comment."""
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return None
        
        old_content = comment.content
        comment.content = content
        comment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(comment)
        
        # Get value for project context
        value = self.db.query(ExtractedValue).filter(
            ExtractedValue.id == comment.extracted_value_id
        ).first()
        
        # Log the update
        self.audit_service.log(
            entity_type="comment",
            entity_id=comment_id,
            action="comment_updated",
            user=author,
            old_value={"content": old_content},
            new_value={"content": content},
            project_id=value.project_id if value else None
        )
        
        return comment
    
    def delete_comment(self, comment_id: int, author: str = "user") -> bool:
        """Delete a comment."""
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return False
        
        value_id = comment.extracted_value_id
        content = comment.content
        
        # Get value for project context before deleting
        value = self.db.query(ExtractedValue).filter(
            ExtractedValue.id == value_id
        ).first()
        
        self.db.delete(comment)
        self.db.commit()
        
        # Log the deletion
        self.audit_service.log(
            entity_type="comment",
            entity_id=comment_id,
            action="comment_deleted",
            user=author,
            old_value={"content": content, "value_id": value_id},
            project_id=value.project_id if value else None
        )
        
        return True
    
    def get_comments_for_value(self, value_id: int) -> list[Comment]:
        """Get all comments for an extracted value."""
        return self.db.query(Comment).filter(
            Comment.extracted_value_id == value_id
        ).order_by(Comment.created_at.asc()).all()
    
    def get_comment_count_for_value(self, value_id: int) -> int:
        """Get comment count for a value."""
        return self.db.query(Comment).filter(
            Comment.extracted_value_id == value_id
        ).count()

