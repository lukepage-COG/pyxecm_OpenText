"""Tests for the OTCS class."""

from unittest.mock import MagicMock, patch

import requests_mock as rm

from pyxecm.otcs import OTCS


def _make_otcs():
    """Create an OTCS instance without hitting the network."""
    return OTCS(
        protocol="http",
        hostname="otcs",
        port=8080,
        username="admin",
        password="password",
    )


class TestOTCSInit:
    def test_basic_initialization(self):
        otcs = _make_otcs()
        assert otcs.hostname() == "otcs"
        assert otcs.config()["protocol"] == "http"
        assert otcs.config()["port"] == 8080

    def test_credentials(self):
        otcs = _make_otcs()
        creds = otcs.credentials()
        assert creds["username"] == "admin"
        assert creds["password"] == "password"

    def test_set_credentials(self):
        otcs = _make_otcs()
        otcs.set_credentials(username="new_user", password="new_pass")
        assert otcs.credentials()["username"] == "new_user"
        assert otcs.credentials()["password"] == "new_pass"

    def test_set_hostname(self):
        otcs = _make_otcs()
        otcs.set_hostname("new-host")
        assert otcs.hostname() == "new-host"

    def test_urls(self):
        otcs = _make_otcs()
        assert "http://otcs:8080" in otcs.base_url()
        assert "/cs/cs" in otcs.cs_url()
        assert "/api" in otcs.rest_url()

    def test_ticket_initially_none(self):
        otcs = _make_otcs()
        assert otcs.otcs_ticket() is None

    def test_set_otcs_ticket(self):
        otcs = _make_otcs()
        otcs.set_otcs_ticket("my-ticket")
        assert otcs.otcs_ticket() == "my-ticket"
        cookie = otcs.cookie()
        assert cookie is not None
        assert cookie.get("otcsticket") == "my-ticket"

    def test_set_otds_ticket(self):
        otcs = _make_otcs()
        otcs.set_otds_ticket("otds-ticket")
        # stored as private attribute _otds_ticket
        assert otcs._otds_ticket == "otds-ticket"

    def test_set_otds_token(self):
        otcs = _make_otcs()
        otcs.set_otds_token("otds-token")
        assert otcs._otds_token == "otds-token"

    def test_partition_and_resource(self):
        otcs = _make_otcs()
        assert otcs.partition_name() == "Content Server Members"
        assert otcs.resource_name() == "cs"

    def test_set_resource_id(self):
        otcs = _make_otcs()
        otcs.set_resource_id("res-123")
        assert otcs.resource_id() == "res-123"


class TestOTCSClassMethods:
    def test_cleanse_item_name(self):
        assert OTCS.cleanse_item_name("test:file") == "testfile"
        assert OTCS.cleanse_item_name("normal_name") == "normal_name"
        assert OTCS.cleanse_item_name("  spaces  ") == "spaces"

    def test_cleanse_item_name_max_length(self):
        result = OTCS.cleanse_item_name("a" * 300, max_length=100)
        assert len(result) <= 100

    def test_date_is_newer_true(self):
        assert OTCS.date_is_newer("2023-01-01T00:00:00", "2024-01-01T00:00:00") is True

    def test_date_is_newer_false(self):
        assert OTCS.date_is_newer("2024-01-01T00:00:00", "2023-01-01T00:00:00") is False


class TestOTCSHeaders:
    def test_request_form_header(self):
        otcs = _make_otcs()
        header = otcs.request_form_header()
        assert "Content-Type" in header
        assert "form-urlencoded" in header["Content-Type"]

    def test_request_json_header(self):
        otcs = _make_otcs()
        header = otcs.request_json_header()
        assert header.get("Content-Type") == "application/json"

    def test_request_download_header(self):
        otcs = _make_otcs()
        header = otcs.request_download_header()
        assert isinstance(header, dict)


class TestOTCSParseResponse:
    def test_parse_valid_json(self):
        otcs = _make_otcs()
        mock_response = MagicMock()
        mock_response.text = '{"results": {"data": {"id": 123}}}'
        result = otcs.parse_request_response(mock_response)
        assert result is not None
        assert result["results"]["data"]["id"] == 123

    def test_parse_none_response(self):
        otcs = _make_otcs()
        result = otcs.parse_request_response(None)
        assert result is None

    def test_parse_empty_text(self):
        otcs = _make_otcs()
        mock_response = MagicMock()
        mock_response.text = ""
        result = otcs.parse_request_response(mock_response)
        assert result is None


class TestOTCSResultHelpers:
    def test_get_result_value(self):
        otcs = _make_otcs()
        response = {
            "results": {
                "data": {
                    "properties": {
                        "id": 42,
                        "name": "Test Node",
                    }
                }
            }
        }
        val = otcs.get_result_value(response=response, key="id")
        assert val == 42

    def test_get_result_value_missing_key(self):
        otcs = _make_otcs()
        response = {
            "results": {
                "data": {
                    "properties": {
                        "id": 42,
                    }
                }
            }
        }
        val = otcs.get_result_value(response=response, key="nonexistent")
        assert val is None

    def test_get_result_value_none_response(self):
        otcs = _make_otcs()
        val = otcs.get_result_value(response=None, key="id")
        assert val is None

    def test_exist_result_item(self):
        otcs = _make_otcs()
        response = {
            "results": [
                {"data": {"properties": {"name": "first"}}},
                {"data": {"properties": {"name": "target"}}},
            ]
        }
        result = otcs.exist_result_item(response=response, key="name", value="target")
        assert result is not None

    def test_lookup_result_value(self):
        otcs = _make_otcs()
        response = {
            "results": [
                {"data": {"properties": {"name": "node_a", "id": 10}}},
                {"data": {"properties": {"name": "node_b", "id": 20}}},
            ]
        }
        result = otcs.lookup_result_value(
            response=response,
            key="name",
            value="node_b",
            return_key="id",
        )
        assert result == 20


class TestOTCSAuthentication:
    def test_authenticate_with_username_password(self):
        otcs = _make_otcs()
        with rm.Mocker() as m:
            m.get(
                "http://otcs:8080/cs/cs/api/v1/serverinfo",
                json={"results": {"data": {"server": {"version": "24.4"}}}},
            )
            m.post(
                "http://otcs:8080/cs/cs/api/v1/auth",
                json={"ticket": "new-ticket-abc"},
            )
            result = otcs.authenticate(wait_for_ready=False)
            assert result is not None
            assert otcs.otcs_ticket() == "new-ticket-abc"

    def test_authenticate_reuses_existing_ticket(self):
        otcs = _make_otcs()
        otcs.set_otcs_ticket("existing-ticket")
        result = otcs.authenticate()
        assert result is not None
        assert otcs.otcs_ticket() == "existing-ticket"


class TestOTCSNodeOperations:
    def _authenticated_otcs(self, mock):
        otcs = _make_otcs()
        otcs.set_otcs_ticket("test-ticket")
        return otcs

    def test_get_server_info(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs(m)
            m.get(
                "http://otcs:8080/cs/cs/api/v1/serverinfo",
                json={
                    "server": {"version": "24.4"},
                },
            )
            result = otcs.get_server_info()
            assert result is not None
            assert "server" in result

    def test_get_server_version(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs(m)
            m.get(
                "http://otcs:8080/cs/cs/api/v1/serverinfo",
                json={
                    "server": {"version": "24.4"},
                },
            )
            version = otcs.get_server_version()
            assert version == "24.4"

    def test_get_node(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs(m)
            m.register_uri(
                "GET",
                rm.ANY,
                json={
                    "results": {
                        "data": {
                            "properties": {
                                "id": 12345,
                                "name": "Test Folder",
                                "type": 0,
                            }
                        }
                    }
                },
            )
            result = otcs.get_node(node_id=12345)
            assert result is not None
            assert result["results"]["data"]["properties"]["id"] == 12345

    def test_get_node_by_parent_and_name(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs(m)
            m.register_uri(
                "GET",
                rm.ANY,
                json={
                    "results": [
                        {
                            "data": {
                                "properties": {
                                    "id": 999,
                                    "name": "Target",
                                    "parent_id": 100,
                                }
                            }
                        }
                    ]
                },
            )
            result = otcs.get_node_by_parent_and_name(parent_id=100, name="Target")
            assert result is not None

    def test_delete_node(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs(m)
            m.register_uri(
                "DELETE",
                rm.ANY,
                json={"results": {"data": {}}},
            )
            result = otcs.delete_node(node_id=12345)
            assert result is not None

    def test_get_current_user(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs(m)
            m.register_uri(
                "GET",
                rm.ANY,
                json={
                    "results": {
                        "data": {
                            "id": 1000,
                            "name": "Admin",
                        }
                    }
                },
            )
            result = otcs.get_current_user()
            assert result is not None

    def test_search(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs(m)
            m.register_uri(
                "POST",
                rm.ANY,
                json={
                    "results": [],
                    "collection": {"paging": {"total_count": 0}},
                },
            )
            result = otcs.search(search_term="test*")
            assert result is not None


class TestOTCSUserOperations:
    def _authenticated_otcs(self):
        otcs = _make_otcs()
        otcs.set_otcs_ticket("test-ticket")
        return otcs

    def test_get_user(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs()
            m.register_uri(
                "GET",
                rm.ANY,
                json={
                    "results": {
                        "data": {
                            "properties": {
                                "id": 2000,
                                "name": "testuser",
                                "type": 0,
                            }
                        }
                    }
                },
            )
            result = otcs.get_user(name="testuser")
            assert result is not None

    def test_add_user(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs()
            m.register_uri(
                "POST",
                rm.ANY,
                json={
                    "results": {
                        "data": {
                            "properties": {
                                "id": 3000,
                                "name": "newuser",
                            }
                        }
                    }
                },
            )
            result = otcs.add_user(
                name="newuser",
                password="testpass",
                first_name="New",
                last_name="User",
                email="new@example.com",
                title="Mr.",
                base_group="DefaultGroup",
            )
            assert result is not None

    def test_get_groups(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs()
            m.register_uri(
                "GET",
                rm.ANY,
                json={
                    "results": [],
                    "collection": {"paging": {"total_count": 0}},
                },
            )
            result = otcs.get_groups()
            assert result is not None

    def test_add_group(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs()
            m.register_uri(
                "POST",
                rm.ANY,
                json={
                    "results": {
                        "data": {
                            "properties": {
                                "id": 4000,
                                "name": "TestGroup",
                            }
                        }
                    }
                },
            )
            result = otcs.add_group(name="TestGroup")
            assert result is not None


class TestOTCSWorkspaceOperations:
    def _authenticated_otcs(self):
        otcs = _make_otcs()
        otcs.set_otcs_ticket("test-ticket")
        return otcs

    def test_get_workspace_types(self):
        with rm.Mocker() as m:
            otcs = self._authenticated_otcs()
            m.register_uri(
                "GET",
                rm.ANY,
                json={
                    "results": {
                        "data": {
                            "workspace_types": []
                        }
                    }
                },
            )
            result = otcs.get_workspace_types()
            assert result is not None
