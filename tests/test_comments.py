import pytest
from fastapi.testclient import TestClient
from main import app
from app.src.schemas import CommentUpdate

client = TestClient(app)


@pytest.mark.parametrize("text", ["New comment", "Updated comment"])
def test_update_comment(text):
    # Отправляем запрос на обновление комментария
    response = client.patch("/comments/1", json={"text": text})

    # Проверяем успешность запроса и ожидаемый текст комментария
    assert response.status_code == 200
    assert response.json()["message"] == "Комментарий успешно обновлен"


def test_delete_comment():
    # Отправляем запрос на удаление комментария
    response = client.delete("/comments/1")

    # Проверяем успешность запроса и ожидаемое сообщение об успешном удалении
    assert response.status_code == 200
    assert response.json()["message"] == "Комментарий успешно удален"
