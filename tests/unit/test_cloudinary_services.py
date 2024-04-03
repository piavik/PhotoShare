import unittest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import cloudinary.uploader

import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
load_dotenv()

from app.src.conf.config import settings
from app.src.services.cloudinary_services import (
    upload_photo,
    delete_photo,
    transformed_photo_url,
)  


class TestCloudinaryService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.patcher_upload = patch("app.src.services.cloudinary_services.cloudinary.uploader.upload")
        self.mock_upload = self.patcher_upload.start()

        self.patcher_destroy = patch("app.src.services.cloudinary_services.cloudinary.uploader.destroy")
        self.mock_destroy = self.patcher_destroy.start()

    async def test_upload_photo_success(self):
        self.mock_upload.return_value = {
            "secure_url": "https://res.cloudinary.com/test-image.jpg"
        }
        file = MagicMock()
        result = await upload_photo(file)
        self.assertEqual(
            result, {"secure_url": "https://res.cloudinary.com/test-image.jpg"}
        )

    async def test_upload_photo_failure(self):
        self.mock_upload.side_effect = cloudinary.exceptions.Error("test error")
        file = MagicMock()
        with self.assertRaises(HTTPException) as context:
            await upload_photo(file)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Error uploading image.")

    async def test_delete_photo(self):
        self.mock_destroy.return_value = {"result": "ok"}
        cloudinary_url = "https://res.cloudinary.com/test-image.jpg"
        result = await delete_photo(cloudinary_url)
        self.assertEqual(result, {"result": "ok"})

    async def test_transformed_photo_url(self):
        photo_url = "https://res.cloudinary.com/test-image.jpg"
        filter = "sepia"
        expected_url = f"https://res.cloudinary.com/{settings.cloudinary_name}/image/upload/e_{filter}/test-image.jpg"
        result = await transformed_photo_url(photo_url, filter=filter)
        self.assertEqual(result, expected_url)


if __name__ == "__main__":
    unittest.main()
