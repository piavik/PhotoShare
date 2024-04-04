import unittest
from unittest.mock import MagicMock
from dotenv import load_dotenv

import os
import sys
load_dotenv()
sys.path.append(os.path.abspath('..'))

from sqlalchemy.orm import Session

from app.src.database.models import User
from app.src.schemas import UserModel, RoleOptions
from app.src.repository.users import (
    get_user_by_email,
    create_user,
    update_avatar,
    update_token,
    confirmed_email,
    change_user_role,
    ban_user,
    get_user_by_username,
    change_user_username,
    change_user_email,
    get_users_photos,
    get_users_comments,
    get_active_users)


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, username="test_username", role=RoleOptions.user, banned=False)
        self.refresh_token = 'refresh_token'
        self.email = "test_email@gmail.com"

    async def test_get_user_by_email_found(self):
        user = User(email="test_email@gmail.com")
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email="test_email@gmail.com", db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(email="test_email@gmail.com", db=self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        body = UserModel(username="<NAME>", email="test_email@gmail.com", password="<PASSWORD>")
        result = await create_user(body=body, db=self.session)
        self.assertEqual(body.username, result.username)
        self.assertEqual(body.email, result.email)
        self.assertEqual(body.password, result.password)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_avatar(self):
        user = User(avatar="avatar.com")
        self.session.query().filter().first.return_value = user
        result = await update_avatar(email="test_email@gmail.com", url="avatar.com", db=self.session)
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

    async def test_change_user_role(self):
        self.session.commit.return_value = None
        result = await change_user_role(user=self.user, role=RoleOptions.admin, db=self.session)
        self.assertEqual(result.role, "admin")

    async def test_ban_user(self):
        self.session.commit.return_value = self.user.banned = True
        await ban_user(user=self.user, banned=True, db=self.session)
        self.assertEqual(self.user.banned,  True)

    async def test_get_user_by_username_found(self):
        user = User(username="test_username")
        self.session.query().filter().first.return_value = user
        result = await get_user_by_username(username="test_username", db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_username_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_username(username="test_username", db=self.session)
        self.assertIsNone(result)

    async def test_change_user_username(self):
        self.session.query().filter().first.return_value = self.user
        self.session.commit.return_value = None
        result = await change_user_username(user=self.user, username="changed_username", db=self.session)
        self.assertEqual(result.username, "changed_username")

    async def test_change_user_email(self):
        self.session.query().filter().first.return_value = self.user
        self.session.commit.return_value = None
        result = await change_user_email(user=self.user, email="changed_email@gmail.com", db=self.session)
        self.assertEqual(result.email, "changed_email@gmail.com")

    def test_get_users_photos(self):
        check_list = ["photo1", "photo2", "photo3", "photo4"]
        self.session.query().filter().all.return_value = check_list
        result = get_users_photos(user_id=self.user.id, db=self.session)
        self.assertEqual(result, check_list)

    def test_get_users_comments(self):
        check_list = ["comment1", "comment2", "comment3"]
        self.session.query().filter().all.return_value = check_list
        result = get_users_comments(user_id=self.user.id, db=self.session)
        self.assertEqual(result, check_list)

    async def test_get_active_users(self):
        self.session.query().join().group_by().all.return_value = [self.user]
        result = await get_active_users(db=self.session)
        self.assertEqual(self.user, result[0])


if __name__ == '__main__':
    unittest.main()

