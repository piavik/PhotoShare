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
async def update_comment(
        comment_text: str,
        photo_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db)
    ):
    '''
    Create or update comment
    '''
    comment_to_update = CommentModel(
        text     = comment_text,
        photo_id = photo_id,
        user_id  = current_user.id
    )

    new_comment = await repository_comments.update_comment(db, comment_to_update)

    comment_response = CommentResponse(
        comment = CommentDb(
            text     = comment_text,
            photo_id = photo_id,
            user_id  = current_user.id
        ),
        detail = "Comment updated"

    )
    return comment_response

@router.delete("/{photo_id}/{user_id}", status_code=status.HTTP_200_OK)
async def delete_comment(
        photo_id: int,
        user_id: int,
        current_user: User = Depends(RoleChecker(allowed_roles=["moder"])),
        db: Session = Depends(get_db)
    ):
    '''
    Delete comment
    '''

    result = await repository_comments.delete_comment(db, photo_id, user_id)

    if not result:
         raise HTTPException(status_code=404, detail="Comment does not exist")

    return { "detail": "Comment deleted" }