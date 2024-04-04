from sqlalchemy.orm import Session
from pydantic import ValidationError
from copy import copy

from app.src.database.models import Comment
from app.src.schemas import CommentModel


async def get_comments(photo_id: int, db: Session) -> list[Comment] | None:
    """
    Get specidied user's comment to specified photo from the database

    Args:
        photo_id (int): id of the photo
        db (Session): database session

    Returns:
        list[Comment]: list of comment object
    """    
    comments = db.query(Comment).filter(Comment.photo_id == photo_id).all()

    return comments


async def get_comment_by_user(photo_id: int, user_id: int, db: Session) -> Comment | None:
    """
    Get specidied user's comment to specified photo from the database

    Args:
        photo_id (int): id of the photo
        user_id (int): comment author's id
        db (Session): database session

    Returns:
        Comment: Comment object
    """    
    comment = db.query(Comment).filter(Comment.user_id == user_id, Comment.photo_id == photo_id).first()

    return comment


async def update_comment(update: CommentModel, db: Session) -> Comment:
    """
    Update comment in the database

    Args:
        update (CommentModel): new CommentModel object information for update
        db (Session): database session

    Returns:
        Comment: Comment object
    """
    old_comment = await get_comment_by_user(update.photo_id, update.user_id, db)
    if old_comment:
        new_comment = old_comment
        new_comment.text = update.text
    else:
        new_comment = Comment(**update.dict())

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
