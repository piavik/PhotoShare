from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.src.database.models import Comment
from app.src.schemas import CommentModel


async def update_comment(db: Session, new_comment: CommentModel) -> Comment:
    new_comment = Comment(**new_comment.dict())

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment

async def delete_comment(db: Session, photo_id: int, user_id: int):
    comment = (
        db.query(Comment).filter(Comment.photo_id == photo_id, Comment.user_id == user_id).first()
        )
    if not comment:
        return None
    db.delete(comment)
    db.commit()
    return True


