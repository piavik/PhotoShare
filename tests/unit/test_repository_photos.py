import unittest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.orm import Session

import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
load_dotenv()

from app.src.repository.photos import (
    create_photo,
    edit_photo_tags,
    get_photo_by_id,
    process_tags,
    edit_photo_description,
    delete_photo,
    find_photos,
)
from app.src.schemas import PhotoModel
from app.src.database.models import User, Photo, Tag
from pydantic import ValidationError


class TestPhotosUser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(role="user", id=2)
        self.mock_photo = MagicMock(spec=Photo)
        self.mock_photo._sa_instance_state = MagicMock()
        self.mock_photo.id = 1
        self.mock_photo.tags = []
        self.mock_photo.description = "some test description"

        self.session.query().filter().first.return_value = self.mock_photo

    async def test_create_photo_ok(self):
        tags_list = ["one", "two", "three", "four", "five"]
        photo_model = PhotoModel(
            photo_url="http://example.com/photo.jpg",
            owner_id=self.user.id,
            description="Test ok Photo",
        )
        new_photo = await create_photo(self.session, photo_model, self.user.id, tags_list)

        self.assertIsNotNone(new_photo)
        self.assertEqual(len(new_photo.tags), len(tags_list))
        self.assertEqual(photo_model.photo_url, new_photo.photo_url)
        self.assertEqual(photo_model.owner_id, self.user.id)
        self.assertEqual(photo_model.description, new_photo.description)

    async def test_create_photo_no_tags(self):
        photo_model = PhotoModel(
            photo_url="http://example.com/photo.jpg",
            owner_id=self.user.id,
            description="Test no tags Photo",
        )
        new_photo = await create_photo(
            self.session, photo_model, self.user.id, self.mock_photo.tags
        )

        self.assertIsNotNone(new_photo)
        self.assertFalse(new_photo.tags)
        self.assertEqual(len(new_photo.tags), len(self.mock_photo.tags))
        self.assertEqual(photo_model.photo_url, new_photo.photo_url)
        self.assertEqual(photo_model.owner_id, self.user.id)
        self.assertEqual(photo_model.description, new_photo.description)

    async def test_create_photo_one_tag(self):
        tags_list = ["one"]
        photo_model = PhotoModel(
            photo_url="http://example.com/photo.jpg",
            owner_id=self.user.id,
            description="Test same tags Photo",
        )
        new_photo = await create_photo(self.session, photo_model, self.user.id, tags_list)

        self.assertIsNotNone(new_photo)
        self.assertTrue(new_photo.tags)
        self.assertEqual(len(new_photo.tags), 1)
        self.assertEqual(photo_model.owner_id, self.user.id)
        self.assertEqual(photo_model.description, new_photo.description)

    async def test_get_photo_by_id_found(self):
        photo_id = 1
        self.session.query().filter().first.return_value = self.mock_photo
        photo = await get_photo_by_id(self.session, photo_id)

        self.assertIsNotNone(photo)
        self.assertEqual(photo, self.mock_photo)

    async def test_get_photo_by_id_not_found(self):
        photo_id = 99
        self.session.query().filter().first.return_value = None
        photo = await get_photo_by_id(self.session, photo_id)

        self.assertNotEqual(photo, self.mock_photo)
        self.assertIsNone(photo)

    async def test_edit_photo_tags_ok(self):
        photo_id = 1
        user_id = self.user.id
        new_tags = "updated one two"

        updated_photo = await edit_photo_tags(self.session, photo_id, user_id, new_tags)

        self.assertIsNotNone(updated_photo)
        self.assertTrue(updated_photo.tags)
        self.assertEqual(len(updated_photo.tags), len(new_tags.split()))

    async def test_edit_photo_tags_photo_not_found(self):
        photo_id = 999
        user_id = self.user.id
        new_tags = "updated one two"

        self.session.query.return_value.filter.return_value.first.return_value = None

        updated_photo = await edit_photo_tags(self.session, photo_id, user_id, new_tags)

        self.assertIsNone(updated_photo)

    async def test_edit_photo_no_new_tags(self):
        photo_id = 1
        user_id = self.user.id
        new_tags = " "

        updated_photo = await edit_photo_tags(self.session, photo_id, user_id, new_tags)

        self.assertIsNone(updated_photo)

    def test_process_tags_5_new_ok(self):
        tags_list = ["one", "two", "three", "four", "five"]
        mock_tags = [MagicMock(spec=Tag, name=name) for name in tags_list]

        for tag in mock_tags:
            self.session.query().filter().first.return_value = None

        processed_tags = process_tags(self.session, tags_list)

        self.assertIsNotNone(process_tags)
        self.assertEqual(len(processed_tags), len(tags_list))
        self.assertEqual(len(processed_tags), 5)

    def test_process_tags_1_new_7_existing_ok(self):
        tags_list = ["new", "one", "one", "one", "one", "one", "one", "one"]

        self.session.query.return_value.filter.return_value.first.side_effect = [
            None,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
        ]

        processed_tags = process_tags(self.session, tags_list) #чому повертає список len()==5? 

        self.assertEqual(len(processed_tags), 1)  #очікується, що буде додано тільки перший тег, а решта існують в БД
        self.assertEqual(processed_tags[0].name, "one")
        self.session.commit.assert_called()

    def test_process_tags_all_not_valid(self):
        tags_list = ["one"*50, "two"*50, "three"*50, "four"*50, "five"*50]
        mock_tags = [MagicMock(spec=Tag, name=name) for name in tags_list]

        for tag in mock_tags:
            self.session.query().filter().first.return_value = None

        processed_tags = process_tags(self.session, tags_list)
        self.assertEqual(len(processed_tags), 0)

    def test_process_tags_1_not_valid_5_valid(self):
        tags_list = ["one", "two", "nonvalid"*40, "three", "four", "five"]
        mock_tags = [MagicMock(spec=Tag, name=name) for name in tags_list]

        for tag in mock_tags:
            self.session.query().filter().first.return_value = None

        processed_tags = process_tags(self.session, tags_list)

        self.assertEqual(len(processed_tags), 5)
        self.assertNotIn("nonvalid" * 40, processed_tags)

    def test_process_tags_1_not_valid_1_valid(self):
        tags_list = ["one", "nonvalid"*40]
        mock_tags = [MagicMock(spec=Tag, name=name) for name in tags_list]

        for tag in mock_tags:
            self.session.query().filter().first.return_value = None

        processed_tags = process_tags(self.session, tags_list)
        self.assertEqual(len(processed_tags), 1)
        self.assertNotIn("nonvalid" * 40, processed_tags)

    def test_process_tags_1_not_valid_7_valid(self):
        tags_list = ["one", "two", "nonvalid" * 40, "three", "four", "five", "six", "seven", "eight"]
        mock_tags = [MagicMock(spec=Tag, name=name) for name in tags_list]

        for tag in mock_tags:
            self.session.query().filter().first.return_value = None

        processed_tags = process_tags(self.session, tags_list)
        self.assertEqual(len(processed_tags), 5)
        self.assertNotIn("nonvalid" * 40, processed_tags)

    def test_process_tags_5_same_valid(self):
        tags_list = ["one", "one", "one", "one", "one"]

        mock_tag = MagicMock(spec=Tag, name="one")

        self.session.query.return_value.filter.return_value.first.side_effect = [None, mock_tag, mock_tag, mock_tag, mock_tag]

        processed_tags = process_tags(self.session, tags_list) #чому повертає список len()==5? 

        self.assertEqual(len(processed_tags), 1)  #очікується, що буде додано тільки перший тег, а решта - не унікальні
        self.assertEqual(processed_tags[0].name, "one")
        self.session.add.assert_called_with(mock_tag)
        self.session.commit.assert_called()

    async def test_edit_photo_description_photo_found_new_discr_ok(self):
        new_dicsr = "some new discr"
        self.session.query.return_value.filter.return_value.first.side_effect = self.mock_photo

        edited_photo = await edit_photo_description(self.session, self.mock_photo.id, self.user.id, new_dicsr)

        self.assertTrue(edited_photo)
        self.assertEqual(edited_photo.description, new_dicsr)

    async def test_edit_photo_description_photo_found_new_discr_empty(self):
        new_dicsr = ""
        self.session.query().filter().first.return_value = self.mock_photo

        with self.assertRaises(ValueError) as context:
            await edit_photo_description(
                self.session, self.mock_photo.id, self.user.id, new_dicsr
            )

    async def test_edit_photo_description_photo_not_found(self):
        new_dicsr = "some new discr"
        self.session.query().filter().first.return_value = None

        result = await edit_photo_description(self.session, self.mock_photo.id, self.user.id, new_dicsr)

        self.assertIsNone(result)

    async def test_delete_photo_ok(self):
        result = await delete_photo(self.session, self.mock_photo.id, self.user.id)

        self.assertTrue(result)

    async def test_delete_photo_photo_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await delete_photo(self.session, self.mock_photo.id, self.user.id)

        self.assertIsNone(result)

# додати тести find_photos


if __name__ == "__main__":
    unittest.main()
