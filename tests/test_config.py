import pytest
from pydantic import ValidationError

from config import Settings


PRODUCTION_CONFIG = {
    "ENVIRONMENT": "production",
    "SECRET_KEY": "a-production-secret-with-at-least-32-bytes",
    "GOOGLE_CLIENT_ID": "client.apps.googleusercontent.com",
    "TMDB_API_KEY": "tmdb-test-key",
}


def test_production_requires_strong_secret_key():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, **{**PRODUCTION_CONFIG, "SECRET_KEY": "weak"})


def test_production_requires_google_client_id():
    with pytest.raises(ValidationError, match="GOOGLE_CLIENT_ID"):
        Settings(_env_file=None, **{**PRODUCTION_CONFIG, "GOOGLE_CLIENT_ID": ""})


def test_production_requires_tmdb_credentials():
    with pytest.raises(ValidationError, match="TMDB_API_KEY"):
        Settings(_env_file=None, **{**PRODUCTION_CONFIG, "TMDB_API_KEY": None})


def test_production_rejects_development_secret():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            **{**PRODUCTION_CONFIG, "SECRET_KEY": Settings.DEVELOPMENT_SECRET_KEY},
        )


def test_production_disables_demo_authentication():
    with pytest.raises(ValidationError, match="ALLOW_DEMO_AUTH"):
        Settings(_env_file=None, **{**PRODUCTION_CONFIG, "ALLOW_DEMO_AUTH": True})


def test_development_has_safe_local_defaults():
    settings = Settings(_env_file=None)

    assert settings.ENVIRONMENT == "development"
    assert settings.ALLOW_DEMO_AUTH is False
