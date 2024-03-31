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
    """
    Return information about the current user.

    :param current_user: Data of the current user.
    :type current_user: User
    :return: Return data about the current user.
    :rtype: User
    """
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(),
                             current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                             db: Session = Depends(get_db)):
    """
    Update the avatar of the current user.

    :param file: File to be updated with the avatar.
    :type file: UploadFile
    :param current_user: Data of the current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: Data of the updated user.
    :rtype: User
    """
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
    """
    Change user role by email.

    :param user_email: Email address of the user to change role.
    :type user_email: str
    :param new_role: New role for user.
    :type new_role: str
    :param current_user: Current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: Data about the changed user.
    :rtype: User
    """
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
    """
    Change password to current user.

    :param body: Data to change user password (old_password, new_password).
    :type body: UserPassword
    :param current_user: The user to change password.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: Message that password was changed.
    :rtype: str
    """
    if not auth_service.verify_password(body.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    message = auth_service.update_password(current_user, body.new_password, db)
    red.delete(f"user:{current_user.email}")
    return message


@router.post("/forgot_password")
async def forgot_password(body: UserNewPassword, background_tasks: BackgroundTasks, request: Request,
                          db: Session = Depends(get_db)):
    """
    Request to reset password.

    :param body: Data to reset user password (email, new_password).
    :type body: UserNewPassword
    :param background_tasks: Tasks to run in background.
    :type background_tasks: BackgroundTasks
    :param request: The request to send email.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Message that password was changed.
    :rtype: str
    """
    try:
        user = await repository_users.get_user_by_email(body.email, db)
    except HTTPException:
        return "Email to reset your password was send"
    background_tasks.add_task(send_password_email, user.email, body.new_password, user.username, request.base_url)
    red.delete(f"user:{user.email}")
    return "Email to reset your password was send"


@router.patch('/reset_password/{token}')
async def reset_password(token: str, db: Session = Depends(get_db)):
    """
    Change password to user that request reset password.

    :param token: The token that was sent on email to reset password.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: Message that password was changed.
    :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    password = await auth_service.get_password_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    auth_service.update_password(user, password, db)
    return {"message": "Password reset"}


@router.patch('/ban')
async def ban_user(email: str, current_user: User = Depends(RoleChecker(['admin'])), db: Session = Depends(get_db)):
    """
    Ban user by email.

    :param email: The email of user that will be banned.
    :type email: str
    :param current_user: The current user.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: Message with username of banned user.
    :rtype: str
    """
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    elif user.email == current_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot ban yourself")
    red.delete(f"user:{user.email}")
    return repository_users.ban_user(user, db)


@router.patch('/unban')
async def unban_user(email: str, _: User = Depends(RoleChecker(['admin'])), db: Session = Depends(get_db)):
    """
    Unban user by email.

    :param email: The email of user that will be unbanned.
    :type email: str
    :param _: The current user.
    :type _: User
    :param db: The database session.
    :type db: Session
    :return: Message with username of unbanned user.
    :rtype: str
    """
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="verification error")
    red.delete(f"user:{user.email}")
    return repository_users.unban_user(user, db)
