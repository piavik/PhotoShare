from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
import redis
from app.src.repository import photos as repository_photos

from app.src.database.db import SessionLocal, get_db
from app.src.database.models import User, Photo
from app.src.repository import users as repository_users
from app.src.services.auth import RoleChecker, auth_service
from app.src.conf.config import settings
from app.src.schemas import UserDb, UserPassword, UserNewPassword
from app.src.services.email import send_password_email

router = APIRouter(prefix="/users", tags=["users"])
red = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
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
