import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import date

import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
load_dotenv()

from app.src.repository.rating import (
    rate_photo, 
    get_rates, 
    delete_rate
)
from app.src.database.models import User, Photo, Rate

class TestRateUser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.session.commit = MagicMock()
        self.session.add = MagicMock()
        self.user_id = 17
        self.photo_id = 42
        self.rate_value = 5

        self.user = User(id=self.user_id)
        self.user._sa_instance_state = MagicMock()

        self.photo = Photo(id=self.photo_id, rating=0)
        self.photo._sa_instance_state = MagicMock()

        self.session.query().filter_by().scalar.return_value = self.rate_value
        self.session.query().join().join().filter().first.return_value = None

    async def test_rate_photo_ok(self):

        self.session.query().filter().first.side_effect = [None, self.photo]

        new_rate = await rate_photo(self.session, self.user_id, self.photo_id, self.rate_value)

        self.assertIsNotNone(new_rate)
        self.session.add.assert_called_once()
        self.session.commit.assert_called()
        self.assertEqual(
            self.photo.rating,
            self.rate_value,
        )
        self.assertEqual(
            new_rate.user_id,
            self.user_id,
        )
        self.assertEqual(
            new_rate.photo_id,
            self.photo_id,
        )
        self.assertEqual(
            new_rate.rate,
            self.rate_value,
        )

    async def test_rate_photo_rate_exist(self):
        self.session.query().filter().first.return_value = MagicMock(spec=Rate)
        result = await rate_photo(self.session, self.user_id, self.photo_id, self.rate_value)
        self.assertIsNone(result)

    async def test_get_rates_not_found(self):
        self.session.query().filter().all.return_value = None
        result = await get_rates(self.photo_id, self.session)
        self.assertFalse(result)

    async def test_get_rates_ok(self):
        rate_1 = MagicMock(spec=Rate(id=1))
        rate_2 = MagicMock(spec=Rate(id=2))

        self.session.query().filter().all.return_value = [
            rate_1,
            rate_2,
        ]
        result = await get_rates(self.photo_id, self.session)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, rate_1.id)

    async def test_delete_rate_ok(self):
        rate_1 = MagicMock(spec=Rate(id=1))
        self.session.query().filter().first.return_value = rate_1

        result = await delete_rate(rate_1.id, self.session)
        self.assertTrue(result)

    async def test_delete_rate_not_found(self):
        self.session.query().filter().first.return_value = None

        result = await delete_rate(1, self.session)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
