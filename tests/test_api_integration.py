from fastapi.testclient import TestClient
from app.main import app  # Adjust this import if your FastAPI app is elsewhere

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_fixtures_endpoint():
    response = client.get("/api/v1/fixtures")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Optionally check for expected fields in the first fixture
    if response.json():
        fixture = response.json()[0]
        assert "home_team" in fixture
        assert "away_team" in fixture 