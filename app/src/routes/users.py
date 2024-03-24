from msilib import schema
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
import redis
from app.src.repository import photos as repository_photos

from app.src.database.db import SessionLocal, get_db
from app.src.database.models import User, Photo
from app.src.repository import users as repository_users
from app.src.services.auth import auth_service
from app.src.conf.config import settings
from app.src.schemas import UserDb

router = APIRouter(prefix="/users", tags=["users"])
red = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)


@router.get("/me/", response_model=UserDb)
async def read_users_me(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    return current_user


@router.patch("/avatar", response_model=UserDb)
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )

    r = cloudinary.uploader.upload(
        file.file, public_id=f"NotesApp/{current_user.username}", overwrite=True
    )
    src_url = cloudinary.CloudinaryImage(f"NotesApp/{current_user.username}").build_url(
        width=250, height=250, crop="fill", version=r.get("version")
    )
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    red.delete(f"user:{current_user.email}")
    return user


@router.post("/photos/{photo_id}/rate/", response_model=schema.Photo)
def rate_photo(
    photo_id: int,
    rating: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    # Получаем фотографию по ее идентификатору
    photo = repository_photos.get_photo(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Фотография не найдена")

    # Проверяем, что оценка находится в диапазоне от 1 до 5
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 1 до 5")

    # Проверяем, существует ли уже оценка от данного пользователя для данной фотографии
    user_rating = repository_photos.get_user_photo_rating(db, current_user.id, photo_id)
    if user_rating:
        raise HTTPException(status_code=400, detail="Вы уже оценили эту фотографию")

    # Проверяем, является ли текущий пользователь владельцем фотографии
    if current_user.id == photo.owner_id:
        raise HTTPException(
            status_code=400, detail="Вы не можете оценивать свои фотографии"
        )

    # Проверяем, является ли текущий пользователь администратором или модератором
    if not current_user.is_admin and not current_user.is_moderator:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    # Сохраняем оценку пользователя для фотографии
    repository_photos.create_user_photo_rating(db, current_user.id, photo_id, rating)

    # Обновляем рейтинг фотографии
    photo.update_rating(rating)
    db.commit()

    return photo
