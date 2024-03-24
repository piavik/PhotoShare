from pydantic import BaseModel, Field, EmailStr, ConfigDict, HttpUrl, constr
from datetime import datetime
from typing import Optional, List


class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=20)
    email: EmailStr
    password: str = Field(min_length=6, max_length=20)


class UserDb(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str
    created_at: datetime
    role_id: int
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class PhotoModel(BaseModel):
    photo_url: str
    owner_id: int
    description: str


class PhotoDb(BaseModel):
    id: int
    photo_url: str
    owner_id: int
    description: str
    model_config = ConfigDict(from_attributes=True)


class PhotoResponse(BaseModel):
    photo: PhotoDb
    detail: str = "Photo successfully uploaded"


class TagModel(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=40)
