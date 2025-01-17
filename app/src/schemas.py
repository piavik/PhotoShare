from pydantic import BaseModel, Field, EmailStr, ConfigDict, HttpUrl, constr
from datetime import datetime
from typing import Optional, List
from enum import Enum


class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=20)
    email: EmailStr
    password: str = Field(min_length=6, max_length=20)


class RoleOptions(str, Enum):
    user = "user"
    moder = "moder"
    admin = "admin"


class UserDb(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str
    created_at: datetime
    role: RoleOptions
    model_config = ConfigDict(from_attributes=True)



class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class UserPassword(BaseModel):
    old_password: str = Field(min_length=6, max_length=20)
    new_password: str = Field(min_length=6, max_length=20)


class UserNewPassword(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=6, max_length=20)


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


class PhotoDetailedResponse(BaseModel):
    id: int
    photo_url: HttpUrl
    changed_photo_url: HttpUrl | None
    owner_id: int
    description: Optional[str] = None
    tags: List[TagModel] = []
    rating: float
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SortOptions(str, Enum):
    rating = "rating"
    date = "date"


class ResponceOptions(str, Enum):
    detailed = "detailed"
    url = "url"
    qr_code = "QR code"


class UrlResponse(BaseModel):
    url: HttpUrl


class CommentModel(BaseModel):
    text: str
    photo_id: int
    user_id: int


class CommentDb(BaseModel):
    id: int
    text: str
    photo_id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class CommentResponse(BaseModel):
    comment: CommentDb
    message: str = "Comment updated"


class RateDb(BaseModel):
    id: int
    rate: int
    photo_id: int
    user_id: int


class RateModel(BaseModel):
    rate: int = Field(min_value=1, max_value=5,)
    photo_id: int
    user_id: int


class RateResponse(BaseModel):
    rate: RateDb
    message: str = "Photo's rating updated"


class RatingOptions(int, Enum):
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5
