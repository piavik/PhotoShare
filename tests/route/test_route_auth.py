import pytest
from jose import jwt
from unittest.mock import MagicMock #, patch

from app.src.database.models import User
from app.src.services.auth import auth_service

# @pytest.fixture()
# def token(client, user):
#     response = client.post(
#         "/api/auth/login",
#         data={"username": user.get('email'), "password": user.get('password')},
#     )
#     token = response.json()
#     return token

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
def test_login_ok(client, session, user):
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

def test_login_fail_user_not_found(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": "some@amail.com", "password": user.get("password")},
    )
    assert response.status_code == 401
    data = response.json()
    assert data['detail'] == "Invalid email"

def test_login_fail_wrong_password(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": "abracadabra"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data['detail'] == "Invalid password"

def test_login_fail_user_not_confirmed(client, session, user):
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
def test_refresh_token_ok(client, token02):
    # authenticate via token
    response = client.get(
        "/api/auth/refresh",
        headers={'Authorization': f'Bearer {token02.get("refresh_token")}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data['access_token'], str)
    assert isinstance(data['refresh_token'], str)
    assert data['token_type'] == "bearer"

# def test_refresh_token_fail_user_not_found(client, session, user, monkeypatch):
#     response = client.get(
#         "/api/auth/refresh"
#     )
#     assert response.status_code == 404


# def test_refresh_token_fail_wrong_token_scope(client, session, user, monkeypatch):
#     response = client.get(
#         "/api/auth/refresh"
#     )
#     assert response.status_code == 401

# def test_refresh_token_fail_wrong_token_expired(client, session, user, monkeypatch):
#     response = client.get(
#         "/api/auth/refresh"
#     )
#     assert response.status_code == 401



#---- confirm email ----
# @pytest.fixture
# def mock_get_user_by_email():
#     with patch("get_user_by_email") as mock:
#         yield mock

# @pytest.fixture
# def mock_get_email_from_token():
#     # with patch("auth_service.get_email_from_token") as mock:
#     with patch("get_email_from_token") as mock:     # testing
#         yield mock

def test_confirm_email_ok(client, user):
    token_data = {"sub": user.get("email"), "iat": 1710719280, "exp": 2710719280, "scope": "email_token"}
    token = jwt.encode(token_data, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM)
    response = client.get(
        f"/api/auth/confirmed_email/{token}"
    )
    print(f'{response.text}')
    assert response.status_code == 200
    data = response.json()
    assert data['message'] == "Email confirmed"

def test_confirm_email_ok_already_confirmed(client, user):
    token_data = {"sub": user.get("email"), "iat": 1710719280, "exp": 2710719280, "scope": "email_token"}
    token = jwt.encode(token_data, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM)
    response = client.get(
        f"/api/auth/confirmed_email/{token}"
    )
    print(f'{response.text}')
    assert response.status_code == 200
    data = response.json()
    assert data['message'] == "Your email is already confirmed"

def test_confirm_email_fail_user_not_found(client):
    token_data = {"sub": "some_incorrect_email@here.com", "iat": 1710719280, "exp": 2710719280, "scope": "email_token"}
    token = jwt.encode(token_data, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM)
    response = client.get(
        f"/api/auth/confirmed_email/{token}"
    )
    assert response.status_code == 400
    data = response.json()
    assert data['detail'] == "Verification error"

def test_confirm_email_fail_wrong_token_scope(client, user):
    token_data = {"sub": user.get("email"), "iat": 1710719280, "exp": 2710719280, "scope": "refresh_token"}
    token = jwt.encode(token_data, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM)
    response = client.get(
        f"/api/auth/confirmed_email/{token}"
    )
    assert response.status_code == 422
    data = response.json()
    assert data['detail'] == "Invalid token for email verification"

def test_confirm_email_fail_wrong_token_expired(client, user):
    token_data = {"sub": user.get("email"), "iat": 1710719280, "exp": 1710721280, "scope": "email_token"}
    token = jwt.encode(token_data, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM)
    response = client.get(
        f"/api/auth/confirmed_email/{token}"
    )
    assert response.status_code == 422
    data = response.json()
    assert data['detail'] == "Invalid token for email verification"

#---- request email ----
# def test_request_email_ok(client, user):
#     ...

# def test_request_email_fail_random_string_not_email(client, user):
#     ...

# def test_request_email_fail_user_not_found(client, user):
#     ...

# def test_request_email_fail_user_not_confirmed(client, user):
#     ...


#---- logout ----



if __name__ == "__main__":
    unittest.main()    
    