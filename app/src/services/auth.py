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
            plain_password (str): Plaintext password
            hashed_password (bool): Password hash

        Returns:
            bool: Comparison result of provided hash and calculated hash
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, plain_password):
        """
        Create hash for provided plaintext password

        Args:
            password (str): plaintext password

        Returns:
            str: Hash for provided plaintext password
        """
        return self.pwd_context.hash(plain_password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        """
        Create JWT access token

        Args:
            data (dict): Claims for JWT
            expires_delta (Optional[float], optional): The number of seconds for JWT lifetime. Defaults to None.

        Returns:
            str:  Access token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        """
        Create JWT refresh token

        Args:
            data (dict):  Claims for JWT

        Returns:
            str: Refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
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
            token (str): User's authorization token. Defaults to Depends(oauth2_scheme).
            db (Session): Dependency injection for DB session. Defaults to Depends(get_db).

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
        Create token for email validation

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
            print(e)
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

    def get_user_token(self, token: str = Depends(oauth2_scheme)):
        """
        **Get token for the user**

        Args:
            token (str, optional): [description]. Defaults to Depends(oauth2_scheme).

        Returns:
            [type]: [description]
        """
        return token

    def update_password(self, user: User, new_password: str, db: Session) -> str:
        hashed_password = self.get_password_hash(new_password)
        user.password = hashed_password
        db.commit()
        return "Password was changed"


auth_service = Auth()


class RoleChecker:
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[UserDb, Depends(auth_service.get_current_user)]):
        if ["moder"] == self.allowed_roles:
            self.allowed_roles = ("admin", "moder")
        elif ["user"] == self.allowed_roles:
            self.allowed_roles = ("admin", "moder", "user")
        if user.role in self.allowed_roles:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have enough permissions")

