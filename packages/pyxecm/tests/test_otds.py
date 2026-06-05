"""Tests for the OTDS (OpenText Directory Services) REST client."""

import pytest
import requests
from pyxecm.otds import OTDS


@pytest.fixture
def otds(requests_mock):
    """Create an OTDS instance with mocked HTTP."""
    return OTDS(
        protocol="https",
        hostname="otds.example.com",
        port=443,
        username="admin",
        password="secret",
    )


@pytest.fixture
def rest_url():
    return "https://otds.example.com/otdsws/rest"


class TestOTDSInit:
    def test_default_init(self, otds):
        cfg = otds.config()
        assert cfg["hostname"] == "otds.example.com"
        assert cfg["protocol"] == "https"
        assert cfg["port"] == 443

    def test_credentials(self, otds):
        creds = otds.credentials()
        assert creds["userName"] == "admin"
        assert creds["password"] == "secret"

    def test_config_urls(self, otds):
        cfg = otds.config()
        assert cfg["baseUrl"] == "https://otds.example.com/otdsws"
        assert cfg["restUrl"] == "https://otds.example.com/otdsws/rest"
        assert "credentialUrl" in cfg


class TestOTDSAuthenticate:
    def test_authenticate_with_password(self, otds, requests_mock, rest_url):
        requests_mock.post(
            f"{rest_url}/authentication/credentials",
            json={"ticket": "otds-ticket-abc123"},
        )
        result = otds.authenticate()
        assert result is not None

    def test_authenticate_connection_error(self, otds, requests_mock, rest_url):
        requests_mock.post(
            f"{rest_url}/authentication/credentials",
            exc=requests.exceptions.ConnectionError("Connection refused"),
        )
        result = otds.authenticate()
        assert result is None


class TestOTDSParseResponse:
    def test_parse_valid_json(self, otds):
        mock_response = type("Response", (), {"text": '{"ticket": "abc"}'})()
        result = otds.parse_request_response(mock_response)
        assert result == {"ticket": "abc"}

    def test_parse_none_response(self, otds):
        result = otds.parse_request_response(None)
        assert result is None

    def test_parse_invalid_json(self, otds):
        mock_response = type("Response", (), {"text": "not json"})()
        result = otds.parse_request_response(mock_response, show_error=False)
        assert result is None
