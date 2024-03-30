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
    **Get current user details**
    Authentication required.

    Args:
    - current_user (User, optional): current user. Defaults to Depends(RoleChecker(allowed_roles=["user"])).

    Returns:
    - [UserDb]: user object
    """    
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(),
                             current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                             db: Session = Depends(get_db)):
    """
    **Update user's avatar on Gravatar service.**
    Authentication required.
    Args:
    - file (UploadFile): Avatar picture file. Defaults to File().
    - db (Session): database session. Defaults to Depends(get_db).
    - current_user (UserModel): current user. Defaults to Depends(auth_service.get_current_user).

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


@router.patch("/change_role", response_model=UserDb)
async def change_user_role(user_email: str, new_role: str,
                           current_user: User = Depends(RoleChecker(allowed_roles=["moder"])),
                           db: Session = Depends(get_db)):
    """
    **Chenge user's role**
    Minimal required role^ moderator

    Args:
    - user_email (str): email of the user
    - new_role (str): new role
    - current_user (User, optional):current user. Defaults to Depends(RoleChecker(allowed_roles=["moder"])).
    - db (Session, optional): database session. Defaults to Depends(get_db).

    Raises:
    - HTTPException: 400 This role does not exist
    - HTTPException: 404 User not found
    - HTTPException: 403 Usuficient permissions to modify to admin

    Returns:
    - [UserDb]: user object
    """                           
    if new_role not in ["user", "moder", "admin"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This role does not exist")
    user = await repository_users.get_user_by_email(user_email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.role == "moder" and new_role == "admin" and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Usuficient permissions to modify to admin")
    changed_user = repository_users.change_user_role(user, new_role, db)
    red.delete(f"user:{user.email}")
    return changed_user


@router.patch("/change_password")
async def change_password(body: UserPassword,
                          current_user: User = Depends(RoleChecker(allowed_roles=["user"])),
                          db: Session = Depends(get_db)) -> dict:
    """
    **Change password**

    Args:
    - body (UserPassword): UserPassword object
    - current_user (User, optional): current user. Defaults to Depends(RoleChecker(allowed_roles=["user"])).
    - db (Session, optional): database session. Defaults to Depends(get_db).

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


@router.post("/forgot_password")
async def forgot_password(body: UserNewPassword, background_tasks: BackgroundTasks, request: Request,
                          db: Session = Depends(get_db)) -> dict:
    """
    **Request reset password request endpoint**

    Args:
    - body (UserNewPassword): UserNewPassword object
    - background_tasks (BackgroundTasks): async ring scheduler
    - request (Request): request object
    - db (Session, optional): database session. Defaults to Depends(get_db).

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
    """AI is creating summary for reset_password

    Args:
    - token (str): JWT access token
    - db (Session, optional): database session. Defaults to Depends(get_db).

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


@router.patch('/ban')
async def ban_user(email: str, current_user: User = Depends(RoleChecker(['admin'])), db: Session = Depends(get_db)) -> dict:
    """
    **Endpoint for banning users**
    Admin role required

    Args:
    - email (str): email of the user to ban
    - current_user (User, optional): current user. Defaults to Depends(RoleChecker(['admin'])).
    - db (Session, optional): database session. Defaults to Depends(get_db).

    Raises:
    - HTTPException: 400 Verification error
    - HTTPException: 400 You cannot ban yourself

    Returns:
    - message: message
    """    
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    elif user.email == current_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot ban yourself")
    red.delete(f"user:{user.email}")
    message = repository_users.ban_user(user, db)
    return {"message": message}


@router.patch('/unban')
async def unban_user(email: str, _: User = Depends(RoleChecker(['admin'])), db: Session = Depends(get_db)) -> dict:
    """
    **Unban the user**
    Admin role required

    Args:
    - email (str): email of the user to unban
    - _ (User, optional): admin user. Defaults to Depends(RoleChecker(['admin'])).
        db (Session, optional): database session. Defaults to Depends(get_db).

    Raises:
    - HTTPException: 400 Verification error

    Returns:
    - message: message
    """    
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    red.delete(f"user:{user.email}")
    message = repository_users.unban_user(user, db)
    return {"message": message}
