import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock

from main import app
from app.src.database.db import get_db
from app.src.database.models import Base, User
# from src.models.schemas import UserModel


SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/db.sqlite3"

engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       connect_args={"check_same_thread": False},) 
                       # echo=True)      # debug

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def session():
    # Create the database for tests

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client(session) -> TestClient:
    # Dependency override

    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def user():
    return {"username": "biakabuka", 
            "email": "buka@example.com", 
            "password": "123456789"}

@pytest.fixture(scope="session")
def user2():
    return {"username": "biakabuka", 
            "email": "buka02@example.com", 
            "password": "123456789"}

@pytest.fixture(scope="function", autouse=True)
def patch_fastapi_limiter(monkeypatch):
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock()) 

@pytest.fixture(scope="function")
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    mock_avatar = MagicMock()
    monkeypatch.setattr("app.src.routes.auth.send_email", mock_send_email)
    monkeypatch.setattr("libgravatar.Gravatar", mock_avatar)        # doe not seem to work
    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    token = response.json()
    return token

@pytest.fixture(scope="function")
def token02(client, user2, session, monkeypatch):
    mock_send_email = MagicMock()
    mock_avatar = MagicMock()
    monkeypatch.setattr("app.src.routes.auth.send_email", mock_send_email)
    monkeypatch.setattr("libgravatar.Gravatar", mock_avatar)        # doe not seem to work
    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user2.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user2.get('email'), "password": user2.get('password')},
    )
    token = response.json()
    return token

@pytest.fixture(scope="function")
def admin_token(monkeypatch):
    return "somestring"

@pytest.fixture(scope="function")
def moder_token(monkeypatch):
    return "somestring"

@pytest.fixture(scope="function")
def photo(monkeypatch):
    return {"id": 1,
        "file": "somestring",
        "description": "some description",
        "tags": ["first", "second", "third", "fourth", "fifths" ]
    }
