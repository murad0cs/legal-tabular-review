from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.comment_service import CommentService
from ..schemas import CommentCreate, CommentUpdate, CommentResponse, CommentListResponse

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("/values/{value_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    value_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db)
):
    """Add a comment to an extracted value."""
    service = CommentService(db)
    try:
        comment = service.create_comment(
            value_id=value_id,
            content=data.content,
            author=data.author
        )
        return comment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/values/{value_id}", response_model=CommentListResponse)
def get_comments_for_value(
    value_id: int,
    db: Session = Depends(get_db)
):
    """Get all comments for an extracted value."""
    service = CommentService(db)
    comments = service.get_comments_for_value(value_id)
    return CommentListResponse(comments=comments)


@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db)
):
    """Update a comment."""
    service = CommentService(db)
    comment = service.update_comment(
        comment_id=comment_id,
        content=data.content,
        author="user"  # In a real app, get from auth
    )
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """Delete a comment."""
    service = CommentService(db)
    deleted = service.delete_comment(comment_id, author="user")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

