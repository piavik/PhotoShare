from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.src.schemas import UserResponse, UserModel, TokenModel, RequestEmail
from app.src.database.db import get_db
from app.src.database.models import User
from app.src.repository import users as repository_users
from app.src.services.auth import auth_service, RoleChecker
from app.src.services.email import send_email
from app.src.routes.users import red

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    Sign up a new user.

    :param body: User details.
    :type body: UserModel
    :param background_tasks: Background tasks.
    :type background_tasks: BackgroundTasks
    :param request: Request object.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Dict with user details and message.
    :rtype: Dict
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User created successfully"}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login user.

    :param body: Data of the user to login.
    :type body: OAuth2PasswordRequestForm
    :param db: The database session.
    :type db: Session
    :return: Return dict with access token and refresh token
    :rtype: Dict
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    Refresh access token.

    :param credentials: Authorization credentials.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session.
    :type db: Session
    :return: Return dict with access token and refresh token
    :rtype: dict
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirm email verification.

    :param token: Token used for verification.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: Message that email is confirmed.
    :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Sends an email to confirm email verification.

    :param body: The data of the user to confirm email.
    :type body: RequestEmail
    :param background_tasks: Background tasks.
    :type background_tasks: BackgroundTasks
    :param request: The request to send the email.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Message.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}


@router.post('/logout')
async def logout(token: str = Depends(auth_service.oauth2_scheme),
                 _: User = Depends(RoleChecker(allowed_roles=["user"]))):
    """
    Logout the current user.

    :param token: The access token for the current user.
    :type token: str
    :param _: Current user data.
    :type _: User
    :return: Message that user is logged out.
    :rtype: dict
    """
    red.set(token, 1)
    red.expire(token, 900)
    return {"message": "Logged out"}

