import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
load_dotenv()

from app.src.database.db import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestdConnectDB(unittest.TestCase):
    def test_get_db(self):
        result = get_db()
        self.assertIsNotNone(result)
        another_result = get_db()
        self.assertIsNotNone(another_result)
        self.assertIsNot(result, another_result)

if __name__ == "__main__":
    unittest.main()
