from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.src.database import crud, models


def delete_comment(comment_id: int, current_user: models.User, db: Session) -> None:
    # Получаем комментарий из базы данных
    comment = crud.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    # Проверяем, имеет ли текущий пользователь право удалять комментарий
    if (
        current_user.role != models.UserRole.ADMIN
        and current_user.role != models.UserRole.MODERATOR
    ):
        raise HTTPException(
            status_code=403, detail="У вас нет прав для удаления комментария"
        )

    # Удаляем комментарий из базы данных
    crud.delete_comment(db, comment_id)
