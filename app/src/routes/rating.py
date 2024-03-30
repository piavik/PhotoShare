from sqlalchemy.orm import Session
from app.src.database.models import Rating, Photo


class RatingService:
    def __init__(self, db: Session):
        self.db = db

    def rate_photo(self, user_id: int, photo_id: int, rating: int):
        # Проверяем, существует ли уже оценка от пользователя для данной фотографии
        existing_rating = (
            self.db.query(Rating)
            .filter(Rating.user_id == user_id, Rating.photo_id == photo_id)
            .first()
        )

        # Если оценка уже существует, обновляем ее
        if existing_rating:
            existing_rating.rating = rating
        else:
            # Создаем новую оценку
            new_rating = Rating(user_id=user_id, photo_id=photo_id, rating=rating)
            self.db.add(new_rating)

        # Пересчитываем рейтинг фотографии
        self._update_photo_rating(photo_id)

    def _update_photo_rating(self, photo_id: int):
        # Получаем все оценки для данной фотографии
        ratings = self.db.query(Rating).filter(Rating.photo_id == photo_id).all()

        # Вычисляем новый средний рейтинг
        total_rating = sum(rating.rating for rating in ratings)
        num_ratings = len(ratings)
        new_rating = total_rating / num_ratings if num_ratings > 0 else 0

        # Обновляем рейтинг фотографии
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.rating = new_rating
            self.db.commit()
