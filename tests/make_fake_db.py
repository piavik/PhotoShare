from faker import Faker

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from random import randint

from app.src.database.models import Base, User, Photo
# from tests.conftest import FAKE_PARAMS


SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/db.sqlite3"

engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       connect_args={"check_same_thread": False},) 
                       # echo=True)      # debug

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = TestingSessionLocal()

fake = Faker()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TestUser():
    def __init__(self, num = 0, role = "user"):
        self.username = f"{role}_{num}"
        self.email    = fake.email()
        self.password = f"{self.username}_{self.email}"
        self.role     = role 

    def __call__(self) -> dict:
        return {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "role": self.role
            }

class TestPhoto():
    def __init__(self, total_users = 0):
        self.photo_url   = fake.uri(deep=7)
        self.description = fake.sentence()
        self.owner_id    = randint(1, total_users)
    
    def __call__(self) -> dict:
        return {
            "photo_url": self.photo_url,
            "description": self.description,
            "owner_id": self.owner_id
            }


def make_fake_users(num_users = 1, num_moders = 1, num_admins = 1) -> None:
    users = []
    # fake admins
    for i in range(num_admins):
        users.append(TestUser(i, "admin"))
    # fake users
    for i in range(num_users):
        users.append(TestUser(i))
    # fake moderators
    for i in range(num_moders):
        users.append(TestUser(i, "moder")) 

    # ugly 1 by 1 commit
    for user in users:
        new_user_record = User(**user())
        new_user_record.avatar = ""
        new_user_record.confirmed = True
        new_user_record.password = pwd_context.hash(user.password)
        db.add(new_user_record)
        db.commit()

def make_fake_photos(num_photos, num_users) -> None:
    # fake pictures
    for _ in range(num_photos):
        photo = TestPhoto(num_users)
        new_poto_record = Photo(**photo())
        db.add(new_poto_record)
        db.commit()

# disabled due to circular import issue
# if __name__ == "__main__":
#     make_fake_users(FAKE_PARAMS["users"], FAKE_PARAMS["moders"], FAKE_PARAMS["admins"])
#     make_fake_photos(FAKE_PARAMS["photos"], FAKE_PARAMS["total users"]) 
