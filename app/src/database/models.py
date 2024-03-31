from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Table,
    Column,
    Boolean,
    Float,
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
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photos.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating = Column(Integer)  # Добавляем поле для рейтинга

    @classmethod
    def get_comment(cls, session, comment_id):
        return session.query(cls).get(comment_id)

    def delete_comment(self, session):
        session.delete(self)
        session.commit()


def rate_photo(session, user_id, photo_id, rating):
    from models import Photo, User

    # Получаем информацию о пользователе
    user = session.query(User).get(user_id)

    # Получаем информацию о фотографии
    photo = session.query(Photo).get(photo_id)

    # Проверяем, является ли пользователь модератором или администратором
    if user.role in ["moderator", "admin"]:
        # Создаем новый комментарий с оценкой
        new_comment = Comment(
            text="Rating", photo_id=photo_id, user_id=user_id, rating=rating
        )
        session.add(new_comment)
        session.commit()

        # После выставления новой оценки обновляем средний рейтинг фотографии
        update_photo_ratings(session)

        return "Оценка успешно выставлена"

    # Проверяем, является ли пользователь владельцем фотографии
    if photo.owner_id == user_id:
        return "Вы не можете оценивать свои собственные фотографии"

    # Проверяем, существует ли уже оценка пользователя для данной фотографии
    existing_rating = (
        session.query(Comment)
        .filter(Comment.photo_id == photo_id, Comment.user_id == user_id)
        .first()
    )

    if existing_rating:
        return "Вы уже выставили оценку для этой фотографии"

    # Создаем новый комментарий с оценкой
    new_comment = Comment(
        text="Rating", photo_id=photo_id, user_id=user_id, rating=rating
    )
    session.add(new_comment)
    session.commit()

    # После выставления новой оценки обновляем средний рейтинг фотографии
    update_photo_ratings(session)

    return "Оценка успешно выставлена"


def update_photo_ratings(session):
    from models import Photo, Comment

    # Получаем все фотографии
    photos = session.query(Photo).all()

    for photo in photos:
        # Получаем все комментарии для данной фотографии
        comments = session.query(Comment).filter(Comment.photo_id == photo.id).all()

        # Фильтруем оценки, оставляем только те, которые находятся в диапазоне от 1 до 5
        valid_ratings = [
            comment.rating for comment in comments if 1 <= comment.rating <= 5
        ]

        # Вычисляем средний рейтинг для данной фотографии
        average_rating = (
            sum(valid_ratings) / len(valid_ratings) if valid_ratings else 0.0
        )

        # Обновляем поле rating для фотографии
        photo.rating = average_rating

    # Сохраняем изменения в базе данных
    session.commit()


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
    comments: Mapped[list[Comment]] = relationship("Comment")
    rating: Mapped[Float] = mapped_column(Float, nullable=True, default=0.0)


class User(BaseTable):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[String] = mapped_column(String(50))
    email: Mapped[String] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[String] = mapped_column(String(100), nullable=False)
    role: Mapped[String] = mapped_column(String(20), nullable=False, default="user")
    refresh_token: Mapped[String] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar: Mapped[String] = mapped_column(String(255), nullable=True)
    banned: Mapped[bool] = mapped_column(Boolean, default=False)
