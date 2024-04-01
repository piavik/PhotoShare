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

# logs for testing
#import tests.logging as log
# router = APIRouter(prefix="/auth", tags=["auth"], route_class=log.LoggingRoute)
router = APIRouter(prefix="/auth", tags=["auth"])

security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    **User sign-up endpoint**

    Args:
    - body (UserModel): user info dictionary
    - background_tasks (BackgroundTasks): async ring scheduler
    - request (Request): request object
    - db (Session, optional): database session. Defaults to Depends(get_db).

    Raises:
    - HTTPException: 409 Account already exists

    Returns:
    - UserResponse: execution result
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
    **User login endpoint**

    Args:
    - body (OAuth2PasswordRequestForm, optional): authentication form. Defaults to Depends().
    - db (Session, optional): database session. Defaults to Depends(get_db).

    Raises:
    - HTTPException: 401 Invalid email
    - HTTPException: 401 Email not confirmed
    - HTTPException: 401 Invalid password

    Returns:
    - [TokenModel]: token dictionary {access_token, refresh_token, token_type}
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
    **Refresh access tokens**

    Args:
    - credentials (HTTPAuthorizationCredentials): current refresh token. Defaults to Security(security)
    - db (Session): database session. Defaults to Depends(get_db)

    Raises:
    - HTTPException: 401 Invalid refresh token

    Returns:
    - [TokenModel]: {access_token, refresh_token, token_type}
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
    **API endpoint for email confirmation**

    Correct use: http call by pressing a button in email sent to the user.

    Args:
    - token (str): access token
    - db (Session, optional): database session. Defaults to Depends(get_db).

    Raises:
    - HTTPException: 400 Verification error

    Returns:
    - message: message
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
    **Request email for password reset**

    Args:
    - body (RequestEmail): object with email request parameters
    - background_tasks (BackgroundTasks): async ring scheduler
    - request (Request): request object
    - db (Session, optional): database session. Defaults to Depends(get_db).

    Returns:
    - message: message
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
    **User logut endpoint**

    Args:
    - token (str, optional): [description]. Defaults to Depends(auth_service.oauth2_scheme).
    - _ (User, optional): User object. Defaults to Depends(RoleChecker(allowed_roles=["user"])).

    Returns:
    - message: message
    """                 
    red.set(token, 1)
    red.expire(token, 900)
    return {"message": "Logged out"}

