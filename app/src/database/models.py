from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Table,
    Column,
    Boolean,
    Float,
    UniqueConstraint,
)
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
    id = Column(Integer, primary_key=True)
    text = Column(String(255), nullable=False)
    photo_id = Column(Integer, ForeignKey("photos.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Photo(BaseTable):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    photo_url = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref="photos")
    changed_photo_url = Column(String(255), nullable=True)
    tags = relationship("Tag", secondary="association_table", backref="photos")
    comments = relationship("Comment", backref="photo")
    rating = Column(Float, nullable=True, default=0.0)  # Добавлено поле rating

    def update_rating(self, new_rating: int):
        # Вычисляем новый средний рейтинг
        num_ratings = len(self.comments)
        total_rating = self.rating * num_ratings
        new_total_rating = total_rating + new_rating
        new_average_rating = new_total_rating / (num_ratings + 1)

        # Обновляем рейтинг
        self.rating = new_average_rating


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


class UserPhotoRating(Base):
    __tablename__ = "user_photo_ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    photo_id = Column(Integer, ForeignKey("photos.id"))
    rating = Column(Integer)

    # Уникальный составной ключ для предотвращения дублирования оценок
    __table_args__ = (
        UniqueConstraint("user_id", "photo_id", name="unique_user_photo_rating"),
    )


# 1
