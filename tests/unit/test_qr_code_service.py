from io import BytesIO
import unittest

import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
load_dotenv()

from app.src.services import qr_code_service


class TestQRCodeGeneration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.url = "https://some-test-url.com"

    def test_generate_qr_code_returns_bytes_io(self):
        qr_code_io = qr_code_service.generate_qr_code(self.url)
        self.assertIsInstance(qr_code_io, BytesIO)

    def test_generate_qr_code_non_empty_content(self):
        qr_code_io = qr_code_service.generate_qr_code(self.url)
        content = qr_code_io.getvalue()
        self.assertTrue(len(content) > 0)


if __name__ == "__main__":
    unittest.main()
