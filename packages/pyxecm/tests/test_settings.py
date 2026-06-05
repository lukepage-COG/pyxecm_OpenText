"""Tests for API settings configuration."""


from pyxecm_api.settings import CustomizerAPISettings


class TestCustomizerAPISettings:
    def test_default_settings(self):
        settings = CustomizerAPISettings()
        assert settings.title == "Customizer API"
        assert settings.bind_port == 8000
        assert settings.workers == 1
        assert settings.loglevel == "INFO"
        assert settings.concurrent_payloads == 3

    def test_custom_settings(self):
        settings = CustomizerAPISettings(
            bind_port=9000,
            workers=4,
            loglevel="DEBUG",
        )
        assert settings.bind_port == 9000
        assert settings.workers == 4
        assert settings.loglevel == "DEBUG"

    def test_otds_url_auto_constructed(self):
        settings = CustomizerAPISettings()
        assert settings.otds_url is not None
        assert "otds" in settings.otds_url

    def test_otds_url_explicit(self):
        settings = CustomizerAPISettings(
            OTDS_URL="https://custom-otds:8443",
        )
        assert settings.otds_url == "https://custom-otds:8443"

    def test_api_key_default_none(self):
        settings = CustomizerAPISettings()
        assert settings.api_key is None

    def test_api_key_custom(self):
        settings = CustomizerAPISettings(
            api_key="my-secret-key",
        )
        assert settings.api_key == "my-secret-key"

    def test_temp_dir_default(self):
        settings = CustomizerAPISettings()
        assert "customizer" in settings.temp_dir

    def test_maintenance_page_default(self):
        settings = CustomizerAPISettings()
        assert settings.maintenance_page is True
        assert settings.maintenance_mode is False

    def test_trusted_origins_default(self):
        settings = CustomizerAPISettings()
        assert isinstance(settings.trusted_origins, list)
        assert len(settings.trusted_origins) > 0

    def test_metrics_default(self):
        settings = CustomizerAPISettings()
        assert settings.metrics is True

    def test_reload_default(self):
        settings = CustomizerAPISettings()
        assert settings.reload is False
