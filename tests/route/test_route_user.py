import pytest

from unittest.mock import patch
from jose import jwt

from app.src.database.models import User
from app.src.services.auth import RoleChecker
from app.src.conf.config import settings

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm

#---- me ----
def test_read_users_me_unauthenticated(client):
    response = client.get(
        "/api/users/me"
    )
    assert response.status_code == 401

def test_read_users_me_ok(client, token):
    access_token = token["access_token"]
    payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    email = payload["sub"]
    response = client.get(
        "/api/users/me",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 200
    data = response.json()
    # assert data["username"] == user.get("username")
    assert data["email"] == email


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



if __name__ == "__main__":
    unittest.main()    
    