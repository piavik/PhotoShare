from src.database.models import Comment, User, UserRole
from app.src.services.rating_service import update_comment_rating


def test_update_comment_rating():
    # Создаем пользователей
    user1 = User(id=1, username="user1", role=UserRole.USER)
    user2 = User(id=2, username="user2", role=UserRole.USER)

    # Создаем комментарии
    comment1 = Comment(id=1, user_id=1, text="Comment 1", rating=0)
    comment2 = Comment(id=2, user_id=2, text="Comment 2", rating=0)

    # Обновляем рейтинг первого комментария (предположим, пользователь 2 оценил его)
    update_comment_rating(comment1, user2, 5)

    # Проверяем, что рейтинг обновлен
    assert comment1.rating == 5

    # Обновляем рейтинг второго комментария (предположим, пользователь 1 оценил его)
    update_comment_rating(comment2, user1, 4)

    # Проверяем, что рейтинг второго комментария также обновлен
    assert comment2.rating == 4
