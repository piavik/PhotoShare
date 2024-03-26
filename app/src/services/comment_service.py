from winreg import HKEY_CURRENT_USER

from requests import Session


from app.src.schemas import CommentUpdate
from app.src.database.db import SessionLocal
from app.src.database.models import Comment, User, UserRole
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


# Маршрут для обновления комментария
@router.patch("/comments/{comment_id}")
def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(SessionLocal),
):
    # Получаем комментарий из базы данных по его идентификатору
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    # Проверяем, принадлежит ли комментарий текущему пользователю
    if db_comment.user_id != comment_update.user_id:
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
    current_user: User = Depends(HKEY_CURRENT_USER),
    db: Session = Depends(SessionLocal),
):
    # Получаем комментарий из базы данных по его идентификатору
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    # Проверяем, имеет ли текущий пользователь право удалять комментарий
    if current_user.role != UserRole.ADMIN and current_user.role != UserRole.MODERATOR:
        raise HTTPException(
            status_code=403, detail="У вас нет прав для удаления комментария"
        )

    # Удаляем комментарий из базы данных
    db.delete(db_comment)
    db.commit()

    return {"message": "Комментарий успешно удален"}
