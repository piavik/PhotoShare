from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
import redis

from app.src.database.db import get_db
from app.src.database.models import User
from app.src.repository import users as repository_users
from app.src.services.auth import RoleChecker
from app.src.conf.config import settings
from app.src.schemas import UserDb

router = APIRouter(prefix="/users", tags=["users"])
red = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)


@router.get("/me", response_model=UserDb)
async def read_users_me(current_user: User = Depends(RoleChecker(allowed_roles=["user"]))):
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(),
                             current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                             db: Session = Depends(get_db)):
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'PS_app/{current_user.username}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'PS_app/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    red.delete(f"user:{current_user.email}")
    return user


@router.patch("/change-role", response_model=UserDb)
async def change_user_role(user_email: str, new_role: str,
                           current_user: User = Depends(RoleChecker(allowed_roles=["moder"])),
                           db: Session = Depends(get_db)):
    if new_role not in ["user", "moder", "admin"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This role does not exist")
    user = await repository_users.get_user_by_email(user_email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not founded")
    if current_user.role == "moder" and new_role == "admin" and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You do not have permission to modify to admin")
    changed_user = repository_users.change_user_role(user, new_role, db)
    return changed_user
