import unittest
from jose import jwt
from unittest.mock import MagicMock
from dotenv import load_dotenv

import os
import sys
load_dotenv()
sys.path.append(os.path.abspath('..'))

from sqlalchemy.orm import Session
from app.src.database.models import User
from app.src.services.auth import auth_service


class TestAuth(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, email="test_email@gmail.com", password="test_pass", confirmed=True)
        self.email = "test_email@gmail.com"
        self.password = "password"
        self.hash_password = "$2b$12$PKsdFbF1Ob/DVhKazhTtLOHReegI/kOfPFZCedSaHQKX6AyNye1bO"
        self.access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X2VtYWlsQGdtYWlsLmNvbSIsImlhdCI6MTcxMjA1NjE0MSwiZXhwIjoxODg0ODU2MTQxLCJzY29wZSI6ImFjY2Vzc190b2tlbiJ9.Un0rkbW4jFthpARZKlIldNxEy7YrzCoxjhvvwNs6ayc"
        self.refresh_token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X2VtYWlsQGdtYWlsLmNvbSIsImlhdCI6MTcxMjA1NjIxNCwiZXhwIjoxODg0ODU2MjE0LCJzY29wZSI6InJlZnJlc2hfdG9rZW4ifQ.Hza4jXo7_TFfRAfcVA5H4KKDP3Pl-5woSQ-xP9JXDCA"
        self.password_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X2VtYWlsQGdtYWlsLmNvbSIsInBhc3MiOiJwYXNzd29yZCIsImlhdCI6MTcxMTczMzg1NCwiZXhwIjoxNzEyMzM4NjU0LCJzY29wZSI6InJlZnJlc2hfdG9rZW4ifQ.h0BeHSGFmphCvm8DAD5DWc7VX96GI5bypsSYY6tx418"

    def test_verify_password_correct(self):
        result = auth_service.verify_password(self.password, self.hash_password)
        self.assertTrue(result)

    def test_verify_password_incorrect(self):
        password = "wrong_password"
        result = auth_service.verify_password(password, self.hash_password)
        self.assertFalse(result)

    def test_get_password_hash(self):
        hashed_password = auth_service.get_password_hash(self.password)
        result = auth_service.verify_password(self.password, hashed_password)
        self.assertEqual(result, True)

    async def test_create_access_token(self):
        token = await auth_service.create_access_token(data={"sub": self.email}, expires_delta=500)
        jwt_payload = jwt.decode(token, auth_service.SECRET_KEY, [auth_service.ALGORITHM])
        test_email = jwt_payload['sub']
        self.assertEqual(test_email, self.email)

    async def test_create_refresh_token(self):
        token = await auth_service.create_refresh_token(data={"sub": self.email})
        jwt_payload = jwt.decode(token, auth_service.SECRET_KEY, [auth_service.ALGORITHM])
        test_email = jwt_payload['sub']
        test_scope = jwt_payload['scope']
        self.assertEqual(test_email, self.email)
        self.assertEqual(test_scope, "refresh_token")

    async def test_decode_refresh_token(self):
        email = await auth_service.decode_refresh_token(self.refresh_token)
        self.assertEqual(email, self.email)

    async def test_get_current_user(self):
        self.session.query().filter().first.return_value = self.user
        ver_user = await auth_service.get_current_user(self.access_token, self.session)
        self.assertEqual(ver_user.id, self.user.id)
        self.assertEqual(ver_user.email, self.user.email)

    async def test_create_email_token(self):
        token = await auth_service.create_email_token(data={"sub": self.email})
        jwt_payload = jwt.decode(token, auth_service.SECRET_KEY, [auth_service.ALGORITHM])
        test_email = jwt_payload['sub']
        self.assertEqual(test_email, self.email)

    async def test_get_email_from_token(self):
        email = await auth_service.get_email_from_token(self.refresh_token)
        self.assertEqual(email, self.email)

    async def test_get_password_from_token(self):
        password = await auth_service.get_password_from_token(self.password_token)
        self.assertEqual(password, self.password)

    def test_update_password(self):
        self.session.commit.return_value = None
        auth_service.update_password(self.user, self.password, self.session)
        result = auth_service.verify_password(self.password, self.user.password)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
