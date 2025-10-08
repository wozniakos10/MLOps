from lab01_lib.app import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestFastAPI:
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the ML API"}

    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_invalid_endpoint(self):
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}
