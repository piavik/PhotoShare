from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.src.database.models import Comment
from app.src.schemas import CommentModel


async def create_comment(db: Session, new_comment: CommentModel):
    new_comment = Comment(**new_comment.dict())

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment
