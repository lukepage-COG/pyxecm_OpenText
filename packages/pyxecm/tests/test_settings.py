"""Tests for the Customizer Settings model."""

import tempfile
from pathlib import Path

from pyxecm_customizer.settings import Settings


class TestSettingsDefaults:
    def test_default_log_file(self):
        settings = Settings()
        assert "customizing.log" in settings.cust_log_file
        assert str(Path(tempfile.gettempdir())) in settings.cust_log_file

    def test_default_settings_dir(self):
        settings = Settings()
        assert settings.cust_settings_dir == "/settings/"

    def test_default_stop_on_error(self):
        settings = Settings()
        assert settings.stop_on_error is False

    def test_default_status_file_check(self):
        settings = Settings()
        assert settings.status_file_check is True

    def test_default_profiling(self):
        settings = Settings()
        assert settings.profiling is False

    def test_default_headless_browser(self):
        settings = Settings()
        assert settings.headless_browser is True

    def test_nested_otds_settings(self):
        settings = Settings()
        assert hasattr(settings, "otds")
        assert hasattr(settings.otds, "username")

    def test_nested_otcs_settings(self):
        settings = Settings()
        assert hasattr(settings, "otcs")
        assert hasattr(settings.otcs, "username")


class TestSettingsEnvironmentOverride:
    def test_env_override_stop_on_error(self, monkeypatch):
        monkeypatch.setenv("STOP_ON_ERROR", "true")
        settings = Settings()
        assert settings.stop_on_error is True

    def test_env_nested_override(self, monkeypatch):
        monkeypatch.setenv("OTDS__USERNAME", "custom-admin")
        settings = Settings()
        assert settings.otds.username == "custom-admin"


class TestSettingsFieldTypes:
    def test_placeholder_values_is_dict(self):
        settings = Settings()
        assert isinstance(settings.placeholder_values, dict)
