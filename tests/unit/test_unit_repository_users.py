import unittest
from unittest.mock import MagicMock
from dotenv import load_dotenv

import os
import sys
load_dotenv()
sys.path.append(os.path.abspath('..'))

from sqlalchemy.orm import Session

from app.src.database.models import User
from app.src.schemas import UserModel
from app.src.repository.users import (
    get_user_by_email,
    create_user,
    update_avatar,
    update_token,
    confirmed_email,
    change_user_role,
    ban_user,
    unban_user)


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, role='user', banned = False)
        self.refresh_token = 'refresh_token'
        self.email = "test_email@gmail.com"

    async def test_get_user_by_email_found(self):
        user = User(email="0953226763r@gmail.com")
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email="0953226763r@gmail.com", db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(email="0953226763r@gmail.com", db=self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        body = UserModel(username="<NAME>", email="0953226763r@gmail.com", password="<PASSWORD>")
        result = await create_user(body=body, db=self.session)
        self.assertEqual(body.username, result.username)
        self.assertEqual(body.email, result.email)
        self.assertEqual(body.password, result.password)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_avatar(self):
        user = User(avatar="avatar.com")
        self.session.query().filter().first.return_value = user
        result = await update_avatar(email="0953226763r@gmail.com", url="avatar.com", db=self.session)
        self.assertEqual(result, user)

    async def test_update_token(self):
        self.session.query().filter().first.return_value = self.user
        await update_token(user=self.user, token=self.refresh_token, db=self.session)
        self.assertIsInstance(self.user.refresh_token, str)

    async def test_confirmed_email(self):
        user = User(email=self.email)
        self.session.query().filter().first.return_value = user
        await confirmed_email(email=self.email, db=self.session)
        self.assertEqual(user.confirmed, True)

    def test_change_user_role(self):
        self.session.commit.return_value = None
        result = change_user_role(user=self.user, role="admin", db=self.session)
        self.assertEqual(result.role, "admin")

    def test_ban_user(self):
        self.session.commit.return_value = None
        ban_user(user=self.user, banned=True, db=self.session)
        self.assertEqual(self.user.banned,  True)

    def test_unban_user(self):
        self.user.banned = True
        self.session.commit.return_value = None
        unban_user(user=self.user, banned=False, db=self.session)
        self.assertEqual(self.user.banned,  False)


if __name__ == '__main__':
    unittest.main()

