from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
import redis

from app.src.database.db import get_db
from app.src.database.models import User
from app.src.repository import users as repository_users
from app.src.services.auth import RoleChecker, auth_service
from app.src.conf.config import settings
from app.src.schemas import UserDb, UserPassword, UserNewPassword
from app.src.services.email import send_password_email

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


@router.patch("/change_role", response_model=UserDb)
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
    red.delete(f"user:{user.email}")
    return changed_user


@router.patch("/change_password")
async def change_password(body: UserPassword,
                          current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                          db: Session = Depends(get_db)):
    if not auth_service.verify_password(body.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    message = repository_users.update_password(current_user, body.new_password, db)
    red.delete(f"user:{current_user.email}")
    return message


@router.post("/forgot_password")
async def forgot_password(body: UserNewPassword, background_tasks: BackgroundTasks, request: Request,
                          db: Session = Depends(get_db)):
    try:
        user = await repository_users.get_user_by_email(body.email, db)
    except HTTPException:
        return "Email to reset your password was send"
    background_tasks.add_task(send_password_email, user.email, body.new_password, user.username, request.base_url)
    red.delete(f"user:{user.email}")
    return "Email to reset your password was send"


@router.get('/reset_password/{token}')
async def reset_password(token: str, db: Session = Depends(get_db)):
    email = await auth_service.get_email_from_token(token)
    password = await auth_service.get_password_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    repository_users.update_password(user, password, db)
    return {"message": "Password reset"}
