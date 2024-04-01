from typing import Optional, Annotated
import pickle

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import redis

from app.src.database.db import get_db
from app.src.repository import users as repository_users
from app.src.conf.config import settings
from app.src.schemas import UserDb
from app.src.database.models import User


class Auth:
    '''
    Class for user authentication and JWT generation
    '''
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.jwt_secret_key
    ALGORITHM = settings.jwt_algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        Verify if plain_password corresponds to hashed_password

        Args:
            plain_password (str): Plaintext password to verify.
            hashed_password (bool): Hashed password from the database.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, plain_password):
        """
        Create hash for provided plaintext password

        Args:
            password (str): plaintext password to hash.

        Returns:
            str: Hash for provided plaintext password.
        """
        return self.pwd_context.hash(plain_password)

    async def create_access_token(self, data: dict, expires_delta: int = 15) -> str:
        """
        Create JWT access token

        Args:
            data (dict): Claims for JWT
            expires_delta (int, optional): The number of minutes for JWT lifetime. Default value is 15 minutes.

        Returns:
            str:  Access token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def create_refresh_token(self, data: dict, expires_delta: int = 7) -> str:
        """
        Create a new refresh token

        Args:
            data (dict):  Claims for JWT
            expires_delta (int, optional): Expiration time in days to access token. Default value is 7 days.

        Returns:
            str: Refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=expires_delta)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def decode_refresh_token(self, refresh_token: str) -> str:
        """
        Get user's email from JWT refresh token

        Args:
            refresh_token (str): Refresh token

        Raises:
            HTTPException: 401 Unauthorized. Invalid scope for token
            HTTPException: 401 Unauthorized. Could not validate credentials

        Returns:
            str: User's email
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token")
        except JWTError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Get authenticated user onject

        Args:
            token (str): User's access token.
            db (Session, optional): database session.

        Raises:
            credentials_exception: Custom HTTPException for 401 Unauthorized.

        Returns:
            User: Authenticated user object
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        logout_check = self.r.get(token)
        if logout_check:
            raise credentials_exception
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception
        user = self.r.get(f"user:{email}")
        if not user:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            elif user.banned:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are banned")
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user

    async def create_email_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        """
        Create an email token to send on email verification.

        Args:
            data (dict): Claims for JWT

        Returns:
            str: JWT token that will be sent in email URL
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(minutes=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str) -> str:
        """
        Get user's email from JWT token

        Args:
            token (str): JWT token

        Raises:
            HTTPException: JWT token is invalid

        Returns:
            str: user's emailobtained from JWT token
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")

    async def get_password_from_token(self, token: str) -> str:
        """
        Get reset password from JWT token

        Args:
            token (str): JWT token

        Raises:
            HTTPException: 422 Invalid token for password reset

        Returns:
            str: new password
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            password = payload["pass"]
            return password
        except JWTError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for password reset")

    def update_password(self, user: User, new_password: str, db: Session) -> str:
        """
        Update password to specified user.

        Args:
            user (User): The user to update password.
            new_password (str): The new password.
            db (Session): The database session.

        Returns:
            str: message
        """
        hashed_password = self.get_password_hash(new_password)
        user.password = hashed_password
        db.commit()
        return "Password was changed"


auth_service = Auth()


class RoleChecker:
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[UserDb, Depends(auth_service.get_current_user)]):
        """
        Check if current user's role corresponds to the role in "allowed_roles" parameter

        Args:
            user (Annotated[UserDb, Depends): current user

        Raises:
            HTTPException: 403 Unsufficient permissions

        Returns:
            [type]: [description]
        """        
        if ["moder"] == self.allowed_roles:
            self.allowed_roles = ("admin", "moder")
        elif ["user"] == self.allowed_roles:
            self.allowed_roles = ("admin", "moder", "user")
        if user.role in self.allowed_roles:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsufficient permissions")

