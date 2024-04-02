from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks, Request, Query
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
import redis

from app.src.database.db import get_db
from app.src.database.models import User
from app.src.repository import users as repository_users
from app.src.services.auth import RoleChecker, auth_service
from app.src.conf.config import settings
from app.src.schemas import UserDb, UserPassword, UserNewPassword, RoleOptions
from app.src.services.email import send_password_email, send_email

router = APIRouter(prefix="/users", tags=["users"])
red = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)


@router.get("/me")
async def read_users_me(current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                        db: Session = Depends(get_db)) -> dict:
    """
    **Get current user details**

    Args:
    - current_user (User, optional): current user.

    Returns:
    - user_info: dict with user details
    """
    user_info = {"username": current_user.username,
                 "avatar_url": current_user.avatar,
                 "email": current_user.email,
                 "role": current_user.role,
                 "created_at": current_user.created_at}
    user_info["photos"] = len(repository_users.get_users_photos(current_user, db))
    user_info["comments"] = len(repository_users.get_users_comments(current_user, db))
    return user_info


@router.get("/{username}")
async def read_users(username: str, db: Session = Depends(get_db)) -> dict:
    """
    **Get user details**

    Args:
    - username (str): username of the user.
    - db (Session, optional): database session.

    Returns:
    - user_info: dict with user details
    """
    user = await repository_users.get_user_by_username(username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username")
    user_info = {"username": user.username,
                 "avatar_url": user.avatar,
                 "email": user.email,
                 "role": user.role}
    user_info["photos"] = len(repository_users.get_users_photos(user, db))
    return user_info


@router.patch("/me", response_model=UserDb)
async def update_user(background_tasks: BackgroundTasks, request: Request,
                      token: str = Depends(auth_service.oauth2_scheme),
                      username: str | None = None, email: str | None = None,
                      current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                      db: Session = Depends(get_db)):
    """
    **Change user username or email**

    Args:
    - background_tasks (BackgroundTasks): async ring scheduler.
    - request (Request): request object.
    - token (str): The access token for the current user.
    - username (str, optional): New username for the user. Default is None.
    - email (str, optional): New email for the user. Default is None.
    - current_user (User, optional): current user.
    - db (Session, optional): database session.

    Raises:
    - HTTPException: 409 Username already exists
    - HTTPException: 409 Email already exists

    Returns:
    - [UserDb]: user object
    """
    if username and username != current_user.username:
        user_check_username = await repository_users.get_user_by_username(username, db)
        if user_check_username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        user = await repository_users.change_user_username(current_user, username, db)

    if email and email != current_user.email:
        user_check_email = await repository_users.get_user_by_email(email, db)
        if user_check_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        user = await repository_users.change_user_email(current_user, email, db)
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
        red.delete(f"user:{current_user.email}")
        red.set(token, 1)
        red.expire(token, 900)
    return current_user


@router.patch('/me/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(),
                             current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                             db: Session = Depends(get_db)):
    """
    **Update user's avatar on Gravatar service.**

    Args:
    - file (UploadFile): Avatar picture file.
    - db (Session, optional): database session. 
    - current_user (UserModel, optional): current user.

    Returns:
    - [UserDb]: The user db object that has the avater changed
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


@router.patch("/me/change_password")
async def change_password(body: UserPassword,
                          current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                          db: Session = Depends(get_db)) -> dict:
    """
    **Change password**

    Args:
    - body (UserPassword): UserPassword object.
    - current_user (User, optional): current user.
    - db (Session, optional): database session.

    Raises:
    - HTTPException: 401 Invalid password

    Returns:
    - message: message
    """                          
    if not auth_service.verify_password(body.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    message = auth_service.update_password(current_user, body.new_password, db)
    red.delete(f"user:{current_user.email}")
    return  {"message": message}


@router.post("/me/forgot_password")
async def forgot_password(body: UserNewPassword, background_tasks: BackgroundTasks, request: Request,
                          db: Session = Depends(get_db)) -> dict:
    """
    **Request reset password request endpoint**

    Args:
    - body (UserNewPassword): Data to reset user password (email, new_password).
    - background_tasks (BackgroundTasks): async ring scheduler
    - request (Request): The request to send email.
    - db (Session, optional): database session.

    Returns:
    - message: message
    """                          
    try:
        user = await repository_users.get_user_by_email(body.email, db)
    except HTTPException:
        return "Email to reset your password was send"
    background_tasks.add_task(send_password_email, user.email, body.new_password, user.username, request.base_url)
    red.delete(f"user:{user.email}")
    return  {"message": "Email to reset your password was send"}


@router.patch('/reset_password/{token}')
async def reset_password(token: str, db: Session = Depends(get_db)) -> dict:
    """
    **Reset password endpoint**\n
    Should be called from the URL sent to user's email

    Args:
    - token (str): The token that was sent via email to reset the password.
    - db (Session, optional): database session.

    Raises:
    - HTTPException: 400 Verification error

    Returns:
    - message: message
    """
    email = await auth_service.get_email_from_token(token)
    password = await auth_service.get_password_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    auth_service.update_password(user, password, db)
    return {"message": "Password reset"}


@router.patch("/{user_id}", response_model=UserDb)
async def change_user_role(user_id: int, 
                           new_role: RoleOptions = Query(default=RoleOptions.user),
                           current_user: User = Depends(RoleChecker(allowed_roles=["moder"])),
                           db: Session = Depends(get_db)):
    """
    **Chenge user's role**\n
    Minimal required role: moderator

    Args:
    - user_email (str): email of the user.
    - new_role (RoleOptions): new role.
    - current_user (User, optional):current user.
    - db (Session, optional): database session.

    Raises:
    - HTTPException: 400 You cannot change your own role
    - HTTPException: 403 Usuficient permissions to modify to admin
    - HTTPException: 404 User not found

    Returns:
    - [UserDb]: user object
    """                           
    user = await repository_users.get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own role")
    if current_user.role == "moder" and new_role == "admin" and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Usuficient permissions to modify to admin")
    changed_user = await repository_users.change_user_role(user, new_role, db)
    red.delete(f"user:{user.email}")
    return changed_user


@router.patch('/{user_id}/ban')
async def ban_unban_user(user_id: int, 
                        banned: bool,
                        current_user: User = Depends(RoleChecker(['admin'])),
                        db: Session = Depends(get_db)
                        ) -> dict:
    """
    **Endpoint for banning/unbanning users**\n
    Admin role required

    Args:
    - email (str): email of the user to ban
    - banned (bool): True = banned, False = unbanned
    - current_user (User, optional): current user.
    - db (Session, optional): database session.

    Raises:
    - HTTPException: 400 Verification error
    - HTTPException: 400 You cannot ban yourself

    Returns:
    - message: message
    """    
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot ban/unban yourself")

    user = await repository_users.get_user_by_id(user_id, db)
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    red.delete(f"user:{user.email}")
    message = await repository_users.ban_user(user, banned, db)
    return {"message": message}

