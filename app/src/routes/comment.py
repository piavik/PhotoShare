from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional

from sqlalchemy.orm import Session

from app.src.database.models import User, Comment
from app.src.database.db import SessionLocal
from app.src.schemas import CommentUpdate

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key for JWT token
SECRET_KEY = "123456789"
ALGORITHM = "HS256"


# Function to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # Replace this with your logic to query the user from database
    user = None  # Placeholder for querying the user from the database
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


router = APIRouter()


# Маршрут для обновления комментария
@router.put("/comments/{comment_id}")
def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(SessionLocal),
    current_user: User = Depends(get_current_user),
):
    # Получаем комментарий из базы данных по его идентификатору
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    # Проверяем, принадлежит ли комментарий текущему пользователю
    if db_comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Нельзя редактировать чужой комментарий"
        )

    # Обновляем текст комментария
    db_comment.text = comment_update.text

    # Сохраняем изменения в базе данных
    db.commit()

    return {"message": "Комментарий успешно обновлен"}


# Маршрут для удаления комментария
@router.delete("/comments/{comment_id}")
def delete_comment_route(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(SessionLocal),
):
    # Получаем комментарий из базы данных по его идентификатору
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    # Проверяем, принадлежит ли комментарий текущему пользователю
    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нельзя удалять чужой комментарий")

    # Удаляем комментарий из базы данных
    db.delete(db_comment)
    db.commit()

    return {"message": "Комментарий успешно удален"}
