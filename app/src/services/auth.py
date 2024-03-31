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
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.jwt_secret_key
    ALGORITHM = settings.jwt_algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        Verify the password.

        :param plain_password: Password to verify.
        :type plain_password: str
        :param hashed_password: Hashed password from database.
        :type hashed_password: str
        :return: True if the password is correct, False otherwise.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, plain_password):
        """
        Get the hashed password

        :param password: Password to hash.
        :type password: str
        :return: Hashed password.
        :rtype: str
        """
        return self.pwd_context.hash(plain_password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        """
        Create a new access token.

        :param data: Dict of data.
        :type data: dict
        :param expires_delta: Expiration time in seconds to access token. Default value is 15 minutes.
        :type expires_delta: float, optional
        :return: Access token
        :rtype: str
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
        Create a new refresh token.

        :param data: Dict of data.
        :type data: dict
        :param expires_delta: Expiration time in seconds to access token. Default value is 7 days.
        :type expires_delta: float, optional
        :return: Refresh token
        :rtype: str
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
        Decode a refresh token.

        :param refresh_token: Refresh token to decode.
        :type refresh_token: str
        :return: If refresh token is valid, return email of the user. Otherwise, return None/
        :rtype: str
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
        Get current user information by token.

        :param token: JWT token to get user info.
        :type token: str
        :param db: The database session.
        :type db: Session
        :return: User data or None if token is invalid.
        :rtype: User
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

        :param data: Data to be sent.
        :type data: dict
        :return: A token that can be used to verify email.
        :rtype: str
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
        Get an email address from token.

        :param token: A token that can be used to verify email.
        :type token: str
        :return: An email address if valid, otherwise None.
        :rtype: str
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
        Get a password from token.

        :param token: A token that can be used to take password.
        :type token: str
        :return: A password if valid, otherwise None.
        :rtype: str
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

        :param user: The user to update password.
        :type user: User
        :param new_password: The new password.
        :type new_password: str
        :param db: The database session.
        :type db: Session
        :return: Message.
        :rtype: str
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
        if ["moder"] == self.allowed_roles:
            self.allowed_roles = ("admin", "moder")
        elif ["user"] == self.allowed_roles:
            self.allowed_roles = ("admin", "moder", "user")
        if user.role in self.allowed_roles:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have enough permissions")

