from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.src.database import Base


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Внешний ключ на пользователя
    photo_id = Column(Integer, ForeignKey("photos.id"))  # Внешний ключ на фото
    rating = Column(Integer)  # Оценка от пользователя

    # Связь с пользователем
    user = relationship("User", back_populates="ratings")

    # Связь с фото
    photo = relationship("Photo", back_populates="ratings")
