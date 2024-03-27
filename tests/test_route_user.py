import pytest

from unittest.mock import patch

from app.src.database.models import User
from app.src.services.auth import RoleChecker

#---- me ----
def test_user_info(client, session, user, monkeypatch):
    current_user = user
    # current_user: User = (
    #     session.query(User).filter(User.email == user.get("email")).first()
    # )
    # mock_user = MagicMock()
    monkeypatch.setattr("app.src.services.auth.RoleChecker", current_user)
    response = client.get(
        "/api/user/me"
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user"]["username"] == user.get("username")
    assert data["user"]["email"] == user.get("email")

# def test_avatar(client, session, user, monkeypatch):
#     ...

# def test_change_role_ok_moder_user(client, session, user, monkeypatch):
#     ...

# def test_change_role_ok_admin_user(client, session, user, monkeypatch):
#     ...

# def test_change_role_ok_admin_moder(client, session, user, monkeypatch):
#     ...

# def test_change_role_ok_admin_admin(client, session, user, monkeypatch):
#     ...

# def test_change_role_fail_wrong_role(client, session, user, monkeypatch):
#     ...

# def test_change_role_fail_user_user(client, session, user, monkeypatch):
#     ...

# def test_change_role_fail_user_moder(client, session, user, monkeypatch):
#     ...

# def test_change_role_fail_user_admin(client, session, user, monkeypatch):
#     ...

# def test_change_role_fail_moder_user(client, session, user, monkeypatch):
#     ...
