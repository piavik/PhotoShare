from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.src.conf.config import settings
from app.src.database import models
from fastapi import HTTPException
from app.src.database.db import SessionLocal, Session

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def delete_comment(comment_id: int, current_user: models.User, db: Session) -> None:
    # Получаем комментарий из базы данных
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
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
    db.delete(comment)
    db.commit()


# 5
