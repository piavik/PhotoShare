from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"PhotoShare": "FastAPI group project"}

if __name__ == "__main__":
    unittest.main()    
    