"""Tests for the FastAPI app settings and configuration."""

import tempfile
from pathlib import Path

from pyxecm_api.settings import CustomizerAPISettings


class TestCustomizerAPISettings:
    def test_default_title(self):
        settings = CustomizerAPISettings()
        assert settings.title == "Customizer API"

    def test_default_bind_port(self):
        settings = CustomizerAPISettings()
        assert settings.bind_port == 8000

    def test_default_workers(self):
        settings = CustomizerAPISettings()
        assert settings.workers == 1

    def test_default_temp_dir(self):
        settings = CustomizerAPISettings()
        assert "customizer" in settings.temp_dir
        assert str(Path(tempfile.gettempdir())) in settings.temp_dir

    def test_default_loglevel(self):
        settings = CustomizerAPISettings()
        assert settings.loglevel == "INFO"

    def test_default_namespace(self):
        settings = CustomizerAPISettings()
        assert settings.namespace == "default"

    def test_default_concurrent_payloads(self):
        settings = CustomizerAPISettings()
        assert settings.concurrent_payloads == 3

    def test_default_metrics_enabled(self):
        settings = CustomizerAPISettings()
        assert settings.metrics is True

    def test_default_maintenance_page(self):
        settings = CustomizerAPISettings()
        assert settings.maintenance_page is True

    def test_default_maintenance_mode(self):
        settings = CustomizerAPISettings()
        assert settings.maintenance_mode is False

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("CUSTOMIZER_BIND_PORT", "9000")
        settings = CustomizerAPISettings()
        assert settings.bind_port == 9000

    def test_default_otds_config(self):
        settings = CustomizerAPISettings()
        assert settings.otds_protocol == "http"
        assert settings.otds_host == "otds"
        assert settings.otds_port == 80

    def test_trusted_origins_list(self):
        settings = CustomizerAPISettings()
        assert isinstance(settings.trusted_origins, list)
        assert "http://localhost" in settings.trusted_origins
