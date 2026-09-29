from sqlalchemy.exc import OperationalError

from database.connection import get_db
from main import app


def test_liveness_does_not_depend_on_database(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_responses_include_security_headers(client):
    response = client.get("/health/live")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"


def test_readiness_checks_database(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_503_when_database_is_unavailable(client):
    class UnavailableDatabase:
        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, Exception("database unavailable"))

    def override_get_db():
        yield UnavailableDatabase()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
