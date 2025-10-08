import pytest
from pydantic import ValidationError
from lab01_lib.settings import Settings
from lab01_lib.main import export_envs


class TestSettings:
    """Test suite for the Settings class."""

    def test_settings_load_test(self):
        """ "Test settings with default env file defined in pyproject.toml"""

        settings = Settings()
        assert settings.ENVIRONMENT == "test"
        assert settings.APP_NAME == "lab01_app"
        assert settings.API_KEY == "test-api-key"
        assert settings.DB_PASSWORD == "test-db-password"

    def test_setting_load_prod(self):
        """Test that Settings loads values for the prod environment."""
        export_envs("prod")
        settings = Settings()
        assert settings.ENVIRONMENT == "prod"
        assert settings.APP_NAME == "lab01_app"

    def test_setting_load_dev(self):
        """Test that Settings loads values for the dev environment."""
        export_envs("dev")
        settings = Settings()
        assert settings.ENVIRONMENT == "dev"
        assert settings.APP_NAME == "lab01_app"

    def test_invalid_environment(self):
        """Test that invalid ENVIRONMENT raises a validation error."""
        with pytest.raises(ValueError) as _:
            export_envs("invalid_env")
            Settings()

    def test_invalid_environment_pydantic(self):
        """Test that invalid ENVIRONMENT raises a validation error in pydantic."""
        with pytest.raises(ValidationError) as _:
            Settings(
                ENVIRONMENT="invalid_env",
                APP_NAME="lab01_app",
                API_KEY="test-api-key",
                DB_PASSWORD="test-db-password",
            )
