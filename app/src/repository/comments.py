from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.src.database.models import Comment
from app.src.schemas import CommentModel


async def update_comment(new_comment: CommentModel, db: Session) -> Comment:
    """
    Update comment in the database

    Args:
        new_comment (CommentModel): new CommentModel object
        db (Session): database session

    Returns:
        Comment: Comment object
    """    
    new_comment = Comment(**new_comment.dict())

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment

async def delete_comment(comment_id: int, photo_id: int, db: Session) -> bool:
    """
    Delete comment from the database

    Args:
        comment_id (int): ID of the comment
        photo_id (int): ID of the photo
        db (Session): database session

    Returns:
        bool: result
    """    
    comment = (
        db.query(Comment).filter(Comment.id == comment_id, Comment.photo_id == photo_id).first()
        )
    if not comment:
        return False
    db.delete(comment)
    db.commit()
    return True
