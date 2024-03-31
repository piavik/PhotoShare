import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Photo, Comment, Tag
from main import rate_photo, update_photo_ratings


class TestRatePhoto(unittest.TestCase):
    def setUp(self):
        # Инициализация соединения с базой данных и создание сессии
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

        # Добавление тестовых данных
        self.user = User(
            username="test_user", email="test@example.com", password="password"
        )
        self.session.add(self.user)
        self.session.commit()

        self.photo = Photo(photo_url="test_photo.jpg", owner_id=self.user.id)
        self.session.add(self.photo)
        self.session.commit()

    def test_rate_photo(self):
        # Проверяем, что рейтинг успешно выставлен
        result = rate_photo(self.session, self.user.id, self.photo.id, 4)
        self.assertEqual(result, "Оценка успешно выставлена")

        # Получаем обновленный объект фотографии из базы данных
        updated_photo = self.session.query(Photo).get(self.photo.id)

        # Проверяем, что рейтинг фотографии соответствует ожидаемому значению
        self.assertEqual(updated_photo.rating, 4.0)

    def tearDown(self):
        # Очистка базы данных после выполнения теста
        self.session.rollback()
        self.session.close()


if __name__ == "__main__":
    unittest.main()
