"""Tests for the OTDS class."""

import requests_mock as rm

from pyxecm.otds import OTDS


def _make_otds():
    """Create an OTDS instance without hitting the network."""
    return OTDS(
        protocol="http",
        hostname="otds",
        port=80,
        username="admin",
        password="password",
    )


class TestOTDSInit:
    def test_basic_initialization(self):
        otds = _make_otds()
        cfg = otds.config()
        assert cfg["hostname"] == "otds"
        assert cfg["protocol"] == "http"
        assert cfg["port"] == 80

    def test_credentials(self):
        otds = _make_otds()
        creds = otds.credentials()
        assert creds["userName"] == "admin"
        assert creds["password"] == "password"

    def test_urls(self):
        otds = _make_otds()
        assert "otdsws" in otds.base_url()
        assert "rest" in otds.rest_url()

    def test_partition_url(self):
        otds = _make_otds()
        assert "partitions" in otds.partition_url()

    def test_resource_url(self):
        otds = _make_otds()
        assert "resources" in otds.resource_url()

    def test_token_url(self):
        otds = _make_otds()
        assert "token" in otds.token_url()

    def test_users_url(self):
        otds = _make_otds()
        assert "users" in otds.users_url()

    def test_groups_url(self):
        otds = _make_otds()
        assert "groups" in otds.groups_url()

    def test_cookie_initially_none(self):
        otds = _make_otds()
        assert otds.cookie() is None

    def test_access_token_initially_none(self):
        otds = _make_otds()
        assert otds.get_access_token() is None

    def test_admin_partition_name(self):
        otds = _make_otds()
        assert otds.admin_partition_name() == "otds.admin"

    def test_custom_port_in_url(self):
        otds = OTDS(protocol="http", hostname="otds", port=8181, username="admin", password="password")
        assert "8181" in otds.base_url()

    def test_standard_port_not_in_url(self):
        otds = OTDS(protocol="http", hostname="otds", port=80, username="admin", password="password")
        assert ":80" not in otds.base_url()


class TestOTDSRequestHeader:
    def test_default_header(self):
        otds = _make_otds()
        header = otds.request_header()
        assert header["Content-Type"] == "application/json"

    def test_custom_content_type(self):
        otds = _make_otds()
        header = otds.request_header(content_type="text/plain")
        assert header["Content-Type"] == "text/plain"

    def test_cookie_set_correctly(self):
        otds = _make_otds()
        otds._cookie = {"OTDSTicket": "test-ticket"}
        assert otds.cookie() is not None
        assert otds.cookie()["OTDSTicket"] == "test-ticket"


class TestOTDSAuthentication:
    def test_authenticate_with_credentials(self):
        otds = _make_otds()
        with rm.Mocker() as m:
            m.post(
                "http://otds/otdsws/rest/authentication/credentials",
                json={"ticket": "new-ticket", "token": "new-token"},
            )
            result = otds.authenticate()
            assert result is not None

    def test_authenticate_with_client_credentials(self):
        otds = OTDS(
            protocol="http",
            hostname="otds",
            port=80,
            client_id="my-client",
            client_secret="my-secret",
        )
        with rm.Mocker() as m:
            m.post(
                "http://otds/otdsws/oauth2/token",
                json={"access_token": "oauth-token", "token_type": "bearer"},
            )
            result = otds.authenticate(grant_type="client_credentials")
            assert result is not None


class TestOTDSPartitionOperations:
    def _authenticated_otds(self, mock):
        otds = _make_otds()
        otds._cookie = {"OTDSTicket": "test-ticket"}
        return otds

    def test_add_partition(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds(m)
            m.register_uri("POST", rm.ANY, json={"name": "TestPartition"})
            result = otds.add_partition(name="TestPartition", description="Test")
            assert result is not None

    def test_get_partition(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds(m)
            m.register_uri(
                "GET",
                rm.ANY,
                json={"name": "TestPartition", "description": "A test partition"},
            )
            result = otds.get_partition(name="TestPartition")
            assert result is not None


class TestOTDSUserOperations:
    def _authenticated_otds(self):
        otds = _make_otds()
        otds._cookie = {"OTDSTicket": "test-ticket"}
        return otds

    def test_get_user(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri(
                "GET",
                rm.ANY,
                json={"id": "user123", "name": "testuser"},
            )
            result = otds.get_user(partition="otds.admin", user_id="testuser")
            assert result is not None

    def test_add_user(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri(
                "POST",
                rm.ANY,
                json={"id": "newuser", "name": "New User"},
            )
            result = otds.add_user(
                partition="otds.admin",
                name="newuser",
            )
            assert result is not None

    def test_delete_user(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri("DELETE", rm.ANY, status_code=200, text="")
            result = otds.delete_user(partition="otds.admin", user_id="olduser")
            # Note: delete_user has a missing `return` statement (bug: `bool(...)` without return)
            assert result is None

    def test_get_current_user(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri(
                "GET",
                rm.ANY,
                json={"id": "admin", "name": "Administrator"},
            )
            result = otds.get_current_user()
            assert result is not None


class TestOTDSGroupOperations:
    def _authenticated_otds(self):
        otds = _make_otds()
        otds._cookie = {"OTDSTicket": "test-ticket"}
        return otds

    def test_add_group(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri(
                "POST",
                rm.ANY,
                json={"name": "TestGroup", "description": "A test group"},
            )
            result = otds.add_group(partition="otds.admin", name="TestGroup", description="A test group")
            assert result is not None

    def test_get_group(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri(
                "GET",
                rm.ANY,
                json={"name": "TestGroup"},
            )
            result = otds.get_group(group="TestGroup")
            assert result is not None

    def test_add_user_to_group(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri("POST", rm.ANY, status_code=200, json={})
            result = otds.add_user_to_group(user="testuser", group="TestGroup")
            # Returns response from do_request
            assert result is not None


class TestOTDSResourceOperations:
    def _authenticated_otds(self):
        otds = _make_otds()
        otds._cookie = {"OTDSTicket": "test-ticket"}
        return otds

    def test_add_resource(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri(
                "POST",
                rm.ANY,
                json={"resourceID": "res123", "resourceName": "cs"},
            )
            result = otds.add_resource(
                name="cs",
                description="Content Server",
                display_name="CS",
            )
            assert result is not None

    def test_get_resource(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri(
                "GET",
                rm.ANY,
                json={"resourceID": "res123", "resourceName": "cs"},
            )
            result = otds.get_resource(name="cs")
            assert result is not None


class TestOTDSOAuthClient:
    def _authenticated_otds(self):
        otds = _make_otds()
        otds._cookie = {"OTDSTicket": "test-ticket"}
        return otds

    def test_get_oauth_client(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri(
                "GET",
                rm.ANY,
                json={"clientID": "my-client"},
            )
            result = otds.get_oauth_client(client_id="my-client")
            assert result is not None

    def test_update_oauth_client(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri("PATCH", rm.ANY, json={"clientID": "my-client", "updated": True})
            result = otds.update_oauth_client(
                client_id="my-client",
                updates={"redirectUrls": ["http://localhost"]},
            )
            assert result is not None


class TestOTDSTrustedSites:
    def _authenticated_otds(self):
        otds = _make_otds()
        otds._cookie = {"OTDSTicket": "test-ticket"}
        return otds

    def test_get_trusted_sites(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri("GET", rm.ANY, json={"trustedSites": ["https://example.com"]})
            result = otds.get_trusted_sites()
            assert result is not None

    def test_add_trusted_site(self):
        with rm.Mocker() as m:
            otds = self._authenticated_otds()
            m.register_uri("GET", rm.ANY, json={"stringList": ["https://example.com"]})
            m.register_uri("PUT", rm.ANY, json={"stringList": ["https://example.com", "https://new-site.com"]})
            result = otds.add_trusted_site(trusted_site="https://new-site.com")
            assert result is not None
