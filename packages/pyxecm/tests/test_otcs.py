"""Unit tests for pyxecm.otcs module."""

import pytest
import requests
from pyxecm.otcs import OTCS


class TestOTCSInit:
    """Tests for OTCS.__init__()."""

    def test_init_basic(self):
        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        config = otcs.config()
        assert config["hostname"] == "otcs.test"
        assert config["protocol"] == "http"
        assert config["port"] == 8080
        assert config["username"] == "admin"

    def test_init_defaults(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        config = otcs.config()
        assert "cs/cs" in config["csUrl"]
        assert "cssupport" in config["supportUrl"]

    def test_init_custom_paths(self):
        otcs = OTCS(
            protocol="https",
            hostname="otcs.test",
            port=443,
            base_path="/cs/cs.exe",
            support_path="/cssupport.exe",
        )
        config = otcs.config()
        assert "/cs/cs.exe" in config["csUrl"]
        assert "/cssupport.exe" in config["supportUrl"]

    def test_init_with_otds_ticket(self):
        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            otds_ticket="ticket-abc",
        )
        assert otcs.otcs_ticket() is None  # otcs_ticket not set until authenticate

    def test_config_urls(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        config = otcs.config()
        assert "authenticationUrl" in config
        assert "otcs.test:8080" in config["authenticationUrl"]


class TestOTCSProperties:
    """Tests for OTCS property methods."""

    def test_config_returns_dict(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        assert isinstance(otcs.config(), dict)

    def test_cookie_none_before_auth(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        assert otcs.cookie() is None

    def test_otcs_ticket_none_before_auth(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        assert otcs.otcs_ticket() is None

    def test_credentials(self):
        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        creds = otcs.credentials()
        assert creds["username"] == "admin"
        assert creds["password"] == "secret"

    def test_set_otcs_ticket(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        otcs.set_otcs_ticket("new-ticket")
        assert otcs.otcs_ticket() == "new-ticket"
        assert otcs.cookie() is not None

    def test_set_otds_ticket(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        otcs.set_otds_ticket("otds-ticket")

    def test_request_form_header(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        header = otcs.request_form_header()
        assert "Content-Type" in header
        assert header["Content-Type"] == "application/x-www-form-urlencoded"


class TestOTCSAuthenticate:
    """Tests for OTCS.authenticate()."""

    def test_authenticate_with_username_password(self, requests_mock):
        requests_mock.post(
            "http://otcs.test:8080/cs/cs/api/v1/auth",
            json={"ticket": "auth-ticket-123"},
        )

        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        result = otcs.authenticate(wait_for_ready=False)

        assert result is not None
        assert otcs.otcs_ticket() == "auth-ticket-123"

    def test_authenticate_already_authenticated(self, requests_mock):
        requests_mock.post(
            "http://otcs.test:8080/cs/cs/api/v1/auth",
            json={"ticket": "auth-ticket-123"},
        )

        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        otcs.authenticate(wait_for_ready=False)

        result = otcs.authenticate(wait_for_ready=False)
        assert result is not None
        assert requests_mock.call_count == 1

    def test_authenticate_no_credentials(self):
        otcs = OTCS(protocol="http", hostname="otcs.test", port=8080)
        result = otcs.authenticate(wait_for_ready=False)
        assert result is None

    def test_authenticate_connection_error(self, requests_mock):
        requests_mock.post(
            "http://otcs.test:8080/cs/cs/api/v1/auth",
            exc=requests.ConnectionError("Connection refused"),
        )

        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        result = otcs.authenticate(wait_for_ready=False)
        assert result is None

    def test_authenticate_with_otds_ticket(self, requests_mock):
        requests_mock.get(
            "http://otcs.test:8080/cs/cs/api/v1/auth",
            headers={"OTCSTicket": "otcs-from-otds"},
        )

        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            otds_ticket="my-otds-ticket",
        )
        result = otcs.authenticate(wait_for_ready=False)

        assert result is not None
        assert otcs.otcs_ticket() == "otcs-from-otds"


class TestOTCSDoRequest:
    """Tests for OTCS.do_request() method."""

    def test_do_request_get(self, requests_mock):
        requests_mock.post(
            "http://otcs.test:8080/cs/cs/api/v1/auth",
            json={"ticket": "test-ticket"},
        )
        requests_mock.get(
            "http://otcs.test:8080/cs/cs/api/v2/nodes/1234",
            json={"results": {"data": {"properties": {"id": 1234, "name": "TestNode"}}}},
        )

        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        otcs.authenticate(wait_for_ready=False)

        result = otcs.do_request(
            url="http://otcs.test:8080/cs/cs/api/v2/nodes/1234",
            method="GET",
            headers=otcs.request_form_header(),
        )

        assert result is not None

    def test_do_request_post(self, requests_mock):
        requests_mock.post(
            "http://otcs.test:8080/cs/cs/api/v1/auth",
            json={"ticket": "test-ticket"},
        )
        requests_mock.post(
            "http://otcs.test:8080/cs/cs/api/v2/nodes",
            json={"results": {"data": {"properties": {"id": 9999}}}},
        )

        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        otcs.authenticate(wait_for_ready=False)

        result = otcs.do_request(
            url="http://otcs.test:8080/cs/cs/api/v2/nodes",
            method="POST",
            headers=otcs.request_form_header(),
            data={"type": 0, "name": "TestFolder"},
        )

        assert result is not None

    def test_do_request_unauthenticated(self):
        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        result = otcs.do_request(
            url="http://otcs.test:8080/cs/cs/api/v2/nodes/1",
            method="GET",
            headers={"Content-Type": "application/json"},
        )
        assert result is None


class TestOTCSNodeOperations:
    """Tests for OTCS node CRUD operations."""

    def test_get_server_info(self, requests_mock):
        requests_mock.post(
            "http://otcs.test:8080/cs/cs/api/v1/auth",
            json={"ticket": "test-ticket"},
        )
        requests_mock.get(
            "http://otcs.test:8080/cs/cs/api/v1/serverinfo",
            json={"server": {"version": "23.3"}},
        )

        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        otcs.authenticate(wait_for_ready=False)

        result = otcs.get_server_info()
        assert result is not None

    def test_get_user(self, requests_mock):
        requests_mock.post(
            "http://otcs.test:8080/cs/cs/api/v1/auth",
            json={"ticket": "test-ticket"},
        )
        requests_mock.get(
            "http://otcs.test:8080/cs/cs/api/v2/members",
            json={
                "results": [
                    {
                        "data": {
                            "properties": {
                                "id": 1000,
                                "first_name": "Admin",
                                "last_name": "User",
                                "name": "admin",
                                "type": 0,
                            }
                        }
                    }
                ]
            },
        )

        otcs = OTCS(
            protocol="http",
            hostname="otcs.test",
            port=8080,
            username="admin",
            password="secret",
        )
        otcs.authenticate(wait_for_ready=False)

        result = otcs.get_user(name="admin")
        assert result is not None


class TestOTCSClassMethods:
    """Tests for OTCS class methods."""

    def test_cleanse_item_name_removes_colon(self):
        result = OTCS.cleanse_item_name("File:Name")
        assert ":" not in result

    def test_cleanse_item_name_max_length(self):
        long_name = "A" * 300
        result = OTCS.cleanse_item_name(long_name, max_length=100)
        assert len(result) <= 100

    @pytest.mark.parametrize(
        ("date_old", "date_new", "expected"),
        [
            ("2024-01-01T00:00:00", "2024-06-01T00:00:00", True),
            ("2024-06-01T00:00:00", "2024-01-01T00:00:00", False),
            ("2024-01-01T00:00:00", "2024-01-01T00:00:00", False),
        ],
    )
    def test_date_is_newer(self, date_old, date_new, expected):
        assert OTCS.date_is_newer(date_old, date_new) == expected
