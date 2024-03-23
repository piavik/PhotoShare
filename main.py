from msilib import schema
from fastapi import FastAPI, Depends, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from mysqlx import Session
from pydantic import BaseModel
import redis.asyncio as redis
import uvicorn

from app.src.database.db import SessionLocal
from app.src.routes import auth, users, photos
from app.src.conf.config import settings
from app.src.database import crud

app = FastAPI()

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(photos.router, prefix="/api")


@app.on_event("startup")
async def startup() -> None:
    r = await redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(r)


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
def read_root() -> dict:
    return {"PhotoShare": "FastAPI group project"}


# Маршрут для обновления комментария
@app.patch("/comments/{comment_id}")
def update_comment(
    comment_id: int,
    comment_update: schema.CommentUpdate,
    db: Session = Depends(SessionLocal),
):
    # Получаем комментарий из базы данных по его идентификатору
    db_comment = crud.get_comment(db, comment_id)
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
