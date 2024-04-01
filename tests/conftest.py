import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock

from main import app
from app.src.database.db import get_db
from app.src.database.models import Base, User, Photo
# from src.models.schemas import UserModel
from app.src.services.auth import auth_service
from random import randint

# from tests.make_fake_db import make_fake_users, make_fake_photos
import tests.make_fake_db as fake_db


SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/db.sqlite3"

engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       connect_args={"check_same_thread": False},) 
                       # echo=True)      # debug

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

FAKE_PARAMS = {
    "user": 5,
    "admin": 5,
    "moder": 5,
    "total users": 15, # users + admin + moders
    "photos": 100
}


@pytest.fixture(scope="function", autouse=True)
def patch_fastapi_limiter(monkeypatch):
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock()) 


@pytest.fixture(scope="module")
def session():
    # Create the database for tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    fake_db.make_fake_users(FAKE_PARAMS["user"], FAKE_PARAMS["moder"], FAKE_PARAMS["admin"])
    fake_db.make_fake_photos(FAKE_PARAMS["photos"], FAKE_PARAMS["total users"])
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
def userN():
    return {"username": "biakabuka", 
            "email": "buka02@example.com", 
            "password": "123456789"}


def _get_random_user(session, role = "user") -> User:
    random_username = f'{role}_{randint(0, FAKE_PARAMS[role])}'
    return session.query(User).filter(User.username == random_username).first()

@pytest.fixture(scope="function")
def photo(session) -> Photo:
    ''' get random photo '''
    random_photo = None
    while not random_photo:
        random_photo_id = randint(0, FAKE_PARAMS["photos"])
        random_photo = session.query(Photo).filter(Photo.id == random_photo_id).first()
    return random_photo

@pytest.fixture(scope="function")
def token(client, session):
    random_user = None
    while not random_user:
        random_user = _get_random_user(session)
    response = client.post(
        "/api/auth/login",
        data={"username": random_user.email, "password": f"{random_user.username}_{random_user.email}"},
    )
    token = response.json()
    return token

@pytest.fixture(scope="function")
def admin_token(client, session):
    random_user = None
    while not random_user:
        random_user = _get_random_user(session, role = "admin")
    response = client.post(
        "/api/auth/login",
        data={"username": random_user.email, "password": f"{random_user.username}_{random_user.email}"},
    )
    token = response.json()
    return token

@pytest.fixture(scope="function")
def moder_token(client, session):
    random_user = None
    while not random_user:
        random_user = _get_random_user(session, role = "moder")
    response = client.post(
        "/api/auth/login",
        data={"username": random_user.email, "password": f"{random_user.username}_{random_user.email}"},
    )
    token = response.json()
    return token
