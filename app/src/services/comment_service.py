from winreg import HKEY_CURRENT_USER

from flask.sessions import SessionMixin
from app.src.database.db import get_db, delete_comment
from app.src.database.models import User
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.delete("/comments/{comment_id}")
def delete_comment_route(
    comment_id: int,
    current_user: User = Depends(HKEY_CURRENT_USER),
    db: SessionMixin = Depends(get_db),
):
    delete_comment(comment_id, current_user, db)
    return {"message": "Комментарий успешно удален"}


# 4
