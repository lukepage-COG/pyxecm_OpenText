"""Tests for the OTAC (OpenText Archive Center) REST client."""

import pytest
import requests
from pyxecm.otac import OTAC


@pytest.fixture
def otac(requests_mock):
    """Create an OTAC instance with mocked HTTP."""
    return OTAC(
        protocol="https",
        hostname="otac.example.com",
        port=443,
        ds_username="dsadmin",
        ds_password="dssecret",
        admin_username="otadmin@otds.admin",
        admin_password="adminsecret",
    )


@pytest.fixture
def base_url():
    return "https://otac.example.com"


class TestOTACInit:
    def test_default_init(self, otac):
        cfg = otac.config()
        assert cfg["hostname"] == "otac.example.com"
        assert cfg["protocol"] == "https"
        assert cfg["port"] == 443

    def test_credentials(self, otac):
        creds = otac.credentials()
        assert "username" in creds


class TestOTACAuthenticate:
    def test_authenticate(self, otac, requests_mock, base_url):
        requests_mock.post(
            f"{base_url}/ot-admin/rest/auth/users/login",
            json=[{}, {"TOKEN": "otac-token-xyz"}],
        )
        result = otac.authenticate()
        assert result == "otac-token-xyz"

    def test_authenticate_connection_error(self, otac, requests_mock, base_url):
        requests_mock.post(
            f"{base_url}/ot-admin/rest/auth/users/login",
            exc=requests.exceptions.ConnectionError("Connection failed"),
        )
        result = otac.authenticate()
        assert result is None


class TestOTACParseResponse:
    def test_parse_valid_json(self, otac):
        mock_response = type("Response", (), {"text": '{"status": "ok"}'})()
        result = otac.parse_request_response(mock_response)
        assert result == {"status": "ok"}

    def test_parse_none_response(self, otac):
        result = otac.parse_request_response(None)
        assert result is None

    def test_parse_invalid_json(self, otac):
        mock_response = type("Response", (), {"text": "invalid"})()
        result = otac.parse_request_response(mock_response, show_error=True)
        assert result is None
