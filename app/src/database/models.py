from sqlalchemy import String, DateTime, ForeignKey, Table, Column, Boolean, Float
from sqlalchemy.orm import declarative_base, mapped_column, Mapped, relationship
from datetime import datetime


Base = declarative_base()

association_table = Table(
    "association_table",
    Base.metadata,
    Column("photos", ForeignKey("photos.id")),
    Column("tags", ForeignKey("tags.id")),
)


class BaseTable(Base):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)


class Comment(BaseTable):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class Photo(BaseTable):
    __tablename__ = "photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    photo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user = relationship("User", backref="photos")
    changed_photo_url: Mapped[str] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[Tag]] = relationship(
        "Tag", secondary="association_table", backref="photos"
    )
    comments: Mapped[list[Comment]] = relationship(
        "Comment", backref="photo"
    )  # Добавлено отношение к комментариям
    rating: Mapped[Float] = mapped_column(Float, nullable=True, default=0.0)


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class User(BaseTable):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[String] = mapped_column(String(50))
    email: Mapped[String] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[String] = mapped_column(String(100), nullable=False)
    role_id: Mapped[Role] = mapped_column(ForeignKey("roles.id"), default=1)
    refresh_token: Mapped[String] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar: Mapped[String] = mapped_column(String(255), nullable=True)
