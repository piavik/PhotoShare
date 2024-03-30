from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException, Query
# from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
# from typing import Optional, List, Union
# from datetime import date


from app.src.schemas import (
    CommentModel,
    CommentResponse
)
from app.src.database.db import get_db
from app.src.database.models import User, Comment
from app.src.schemas import CommentDb
from app.src.repository import comments as repository_comments
from app.src.services.auth import auth_service, RoleChecker
# from app.src.conf.config import settings

router = APIRouter(prefix="/comment", tags=["comments"])

@router.post("/{photo_id}/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
        comment_text: str,
        photo_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db)
    ):
    comment_to_create = CommentModel(
        text     = comment_text,
        photo_id = photo_id,
        user_id  = current_user.id
    )

    new_comment = await repository_comments.create_comment(db, comment_to_create)

    comment_response = CommentResponse(
        comment = CommentDb(
            text     = comment_text,
            photo_id = photo_id,
            user_id  = current_user.id
        ),
        detail = "Comment updated"

    )
    return comment_response

