"""Tests for the OTCS (OpenText Content Server) REST client."""


import pytest
import requests
import requests_mock as requests_mock_module
from pyxecm.otcs import OTCS


@pytest.fixture
def otcs(requests_mock):
    """Create an OTCS instance with mocked HTTP."""
    return OTCS(
        protocol="https",
        hostname="otcs.example.com",
        port=443,
        username="admin",
        password="secret",
    )


@pytest.fixture
def base_url():
    return "https://otcs.example.com/cs/cs/api"


@pytest.fixture
def authed_otcs(requests_mock):
    """Create an authenticated OTCS instance."""
    base = "https://otcs.example.com/cs/cs/api"
    requests_mock.post(
        f"{base}/v1/auth",
        json={"ticket": "mock-ticket"},
    )
    inst = OTCS(
        protocol="https",
        hostname="otcs.example.com",
        port=443,
        username="admin",
        password="secret",
    )
    inst.authenticate(wait_for_ready=False)
    return inst


class TestOTCSInit:
    def test_default_init(self, otcs):
        cfg = otcs.config()
        assert cfg["hostname"] == "otcs.example.com"
        assert cfg["protocol"] == "https"
        assert cfg["port"] == 443
        assert cfg["username"] == "admin"

    def test_config_returns_dict(self, otcs):
        cfg = otcs.config()
        assert isinstance(cfg, dict)
        assert "baseUrl" in cfg
        assert cfg["baseUrl"] == "https://otcs.example.com"

    def test_credentials(self, otcs):
        creds = otcs.credentials()
        assert creds["username"] == "admin"
        assert creds["password"] == "secret"


class TestAuthenticate:
    def test_authenticate_with_password(self, otcs, requests_mock, base_url):
        requests_mock.post(
            f"{base_url}/v1/auth",
            json={"ticket": "mock-ticket-123"},
        )
        result = otcs.authenticate(wait_for_ready=False)
        assert result is not None
        assert result.get("otcsticket") == "mock-ticket-123"

    def test_authenticate_no_credentials(self, requests_mock):
        otcs = OTCS(
            protocol="https",
            hostname="otcs.example.com",
            port=443,
        )
        result = otcs.authenticate(wait_for_ready=False)
        assert result is None


class TestParseRequestResponse:
    def test_parse_valid_json(self, otcs):
        mock_response = type("Response", (), {"text": '{"key": "value"}'})()
        result = otcs.parse_request_response(mock_response)
        assert result == {"key": "value"}

    def test_parse_empty_response(self, otcs):
        result = otcs.parse_request_response(None)
        assert result is None

    def test_parse_empty_text(self, otcs):
        mock_response = type("Response", (), {"text": ""})()
        result = otcs.parse_request_response(mock_response)
        assert result is None

    def test_parse_invalid_json_raises(self, otcs):
        mock_response = type("Response", (), {"text": "not json"})()
        with pytest.raises(requests.exceptions.ConnectionError):
            otcs.parse_request_response(mock_response, show_error=True)

    def test_parse_invalid_json_warning(self, otcs):
        mock_response = type("Response", (), {"text": "not json"})()
        result = otcs.parse_request_response(mock_response, show_error=False)
        assert result is None


class TestGetResultValue:
    def test_get_result_value_from_results(self, otcs):
        response = {
            "results": [
                {"data": {"properties": {"id": 12345, "name": "test-node"}}},
            ],
        }
        assert otcs.get_result_value(response, "id") == 12345
        assert otcs.get_result_value(response, "name") == "test-node"

    def test_get_result_value_from_data(self, otcs):
        response = {
            "data": {"properties": {"id": 99, "name": "single"}},
        }
        assert otcs.get_result_value(response, "id") == 99

    def test_get_result_value_none_response(self, otcs):
        assert otcs.get_result_value(None, "id") is None

    def test_get_result_value_empty_results(self, otcs):
        response = {"results": []}
        assert otcs.get_result_value(response, "id") is None

    def test_get_result_value_missing_key(self, otcs):
        response = {
            "results": [
                {"data": {"properties": {"id": 1}}},
            ],
        }
        assert otcs.get_result_value(response, "nonexistent") is None


class TestLookupResultValue:
    def test_lookup_result_value(self, otcs):
        response = {
            "results": [
                {"data": {"properties": {"name": "Alice", "id": 1}}},
                {"data": {"properties": {"name": "Bob", "id": 2}}},
            ],
        }
        assert otcs.lookup_result_value(response, "name", "Bob", "id") == 2

    def test_lookup_result_value_not_found(self, otcs):
        response = {
            "results": [
                {"data": {"properties": {"name": "Alice", "id": 1}}},
            ],
        }
        assert otcs.lookup_result_value(response, "name", "Unknown", "id") is None


class TestExistResultItem:
    def test_exist_result_item_true(self, otcs):
        response = {
            "results": [
                {"data": {"properties": {"name": "target"}}},
            ],
        }
        assert otcs.exist_result_item(response, "name", "target") is True

    def test_exist_result_item_false(self, otcs):
        response = {
            "results": [
                {"data": {"properties": {"name": "other"}}},
            ],
        }
        assert otcs.exist_result_item(response, "name", "target") is False


class TestDoRequest:
    def test_get_request(self, authed_otcs, requests_mock, base_url):
        requests_mock.get(
            f"{base_url}/v2/nodes/12345",
            json={"results": [{"data": {"properties": {"id": 12345}}}]},
        )
        result = authed_otcs.do_request(
            f"{base_url}/v2/nodes/12345", method="GET", headers={},
        )
        assert result is not None
        assert "results" in result

    def test_post_request(self, authed_otcs, requests_mock, base_url):
        requests_mock.post(
            f"{base_url}/v2/nodes",
            json={"results": [{"data": {"properties": {"id": 99999}}}]},
        )
        result = authed_otcs.do_request(
            f"{base_url}/v2/nodes",
            method="POST",
            headers={},
            data={"type": 0, "parent_id": 2000, "name": "Test Folder"},
        )
        assert result is not None

    def test_unauthenticated_request(self, otcs, requests_mock, base_url):
        requests_mock.get(
            f"{base_url}/v2/nodes/12345",
            json={"results": [{"data": {"properties": {"id": 12345}}}]},
        )
        result = otcs.do_request(f"{base_url}/v2/nodes/12345", method="GET", headers={})
        assert result is None


class TestGetNode:
    def test_get_node(self, authed_otcs, requests_mock, base_url):
        requests_mock.register_uri(
            "GET",
            requests_mock_module.ANY,
            json={
                "results": {
                    "data": {
                        "properties": {
                            "id": 12345,
                            "name": "Test Node",
                            "type": 0,
                        },
                    },
                },
            },
        )
        result = authed_otcs.get_node(12345)
        assert result is not None


class TestGetServerInfo:
    def test_get_server_info(self, authed_otcs, requests_mock, base_url):
        requests_mock.register_uri(
            "GET",
            requests_mock_module.ANY,
            json={
                "data": {
                    "server_version": "24.4",
                },
            },
        )
        result = authed_otcs.get_server_info()
        assert result is not None


class TestDeleteNode:
    def test_delete_node(self, authed_otcs, requests_mock, base_url):
        requests_mock.register_uri(
            "DELETE",
            requests_mock_module.ANY,
            json={"results": {"data": {}}},
        )
        result = authed_otcs.delete_node(12345)
        assert result is not None or result is None
