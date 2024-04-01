from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.src.database.models import Comment
from app.src.schemas import CommentModel


async def update_comment(db: Session, new_comment: CommentModel) -> Comment:
    """
    Update comment in the database

    Args:
        db (Session): database session
        new_comment (CommentModel): new CommentModel object

    Returns:
        Comment: Comment object
    """    
    new_comment = Comment(**new_comment.dict())

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment

async def delete_comment(db: Session, photo_id: int, user_id: int) -> bool:
    """
    Delete comment from the database

    Args:
        db (Session): database session
        photo_id (int): ID of the commented photo
        user_id (int): ID of the user making the comment

    Returns:
        bool: result
    """    
    comment = (
        db.query(Comment).filter(Comment.photo_id == photo_id, Comment.user_id == user_id).first()
        )
    if not comment:
        return False
    db.delete(comment)
    db.commit()
    return True


