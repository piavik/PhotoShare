import pytest
from jose import jwt
from fastapi import HTTPException, status

from unittest.mock import Mock, MagicMock, patch

from app.src.database.models import User
from app.src.repository.users import get_user_by_email
from app.src.services.auth import auth_service


#---- signup ----
def test_signup_ok(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("app.src.services.email.send_email", mock_send_email)
    response = client.post(
        "/api/auth/signup",
        json=user
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["username"] == user.get("username")
    assert data["user"]["email"] == user.get("email")
    assert data["detail"] == "User created successfully"
    assert "password" not in data

def test_signup_fail_existing_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("app.src.services.email.send_email", mock_send_email)
    response = client.post(
        "/api/auth/signup",
        json=user
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"

#---- login ----
def test_login_ok(client, session, user, monkeypatch):
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 200 , response.text
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "password" not in data

def test_login_fail_user_not_found(client, user, monkeypatch):
    response = client.post(
        "/api/auth/login",
        data={"username": "some@amail.com", "password": user.get("password")},
    )
    assert response.status_code == 401
    data = response.json()
    assert data['detail'] == "Invalid email"

def test_login_fail_wrong_password(client, user, monkeypatch):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": "abracadabra"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data['detail'] == "Invalid password"

def test_login_fail_user_not_confirmed(client, session, user, monkeypatch):
    current_user: User = (
        session.query(User).filter(User.email == user.get("email")).first()
    )
    current_user.confirmed = False
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 401
    data = response.json()
    assert data['detail'] == "Email not confirmed"

#---- refresh token ----
# requred user to be authenticated
# def test_refresh_token_ok(client, session, user, monkeypatch):
#     response = client.get(
#         "/api/auth/refresh",
#         data={"username": user.get("email"), "password": user.get("password")},
#     )

#---- confirm email ----
@pytest.fixture
def mock_get_user_by_email():
    with patch("get_user_by_email") as mock:
        yield mock

@pytest.fixture
def mock_get_email_from_token():
    # with patch("auth_service.get_email_from_token") as mock:
    with patch("get_email_from_token") as mock:     # testing
        yield mock

def test_confirm_email_ok(client, session, user, monkeypatch):
    token_data = {"sub": user.get("email"), "iat": 1710719280, "exp": 2710719280, "scope": "email_token"}
    token = jwt.encode(token_data, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM)
    mock_get_user_by_email.return_value = user.get("username")
    mock_get_email_from_token.return_value = user.get("email")
    response = client.get(
        f"/api/auth/confirm_email/{token}"
    )
    print(response.text)
    assert response.status_code == 200
    data = response.json()
    assert data['message'] == "Email verified"

# def test_confirm_email_fail_wrong_token(client, session, user, monkeypatch):
#     token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJidWthQGUuY29tIiwiaWF0IjoxNzEwNzE5MjgwLCJleHAiOjI3MTA3MTkyODAsInNjb3BlIjoiZW1haWxfdG9rZW4ifQ.0MdrnUkIhat0QDR61TcKPqXHbx4RDxN1zsUnmp4i1vg"
#     mock_get_user_by_email.return_value = user.get("username")
#     mock_get_email_from_token.return_value = HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                                                            detail="Invalid token for email verification")
#     response = client.get(
#         f"/api/auth/confirm_email/{token}"
#     )
#     # assert response.status_code == 422
#     data = response.json()
#     assert data['detail'] == "Invalid token for email verification"

#---- request email ----
# def test_request_email_ok(client, session, user, monkeypatch):
#     ...

# def test_request_email_fail_user_not_found(client, session, user, monkeypatch):
#     ...

# def test_request_email_fail_user_not_confirmed(client, session, user, monkeypatch):
#     ...
