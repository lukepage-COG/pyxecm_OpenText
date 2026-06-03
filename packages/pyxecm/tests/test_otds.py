"""Unit tests for pyxecm.otds module."""

import requests
from pyxecm.otds import OTDS


class TestOTDSInit:
    """Tests for OTDS.__init__()."""

    def test_init_basic(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )
        config = otds.config()
        assert config["hostname"] == "otds.test"
        assert config["protocol"] == "http"
        assert config["port"] == 80
        assert config["username"] == "admin"

    def test_init_defaults(self):
        otds = OTDS(protocol="http", hostname="otds.test", port=80)
        config = otds.config()
        assert config["adminPartition"] == "otds.admin"
        assert config["username"] == "admin"

    def test_init_urls(self):
        otds = OTDS(protocol="https", hostname="otds.test", port=443)
        config = otds.config()
        assert config["baseUrl"] == "https://otds.test/otdsws"
        assert config["restUrl"] == "https://otds.test/otdsws/rest"

    def test_init_non_standard_port(self):
        otds = OTDS(protocol="http", hostname="otds.test", port=8080)
        config = otds.config()
        assert "8080" in config["baseUrl"]

    def test_init_with_existing_ticket(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            otds_ticket="pre-ticket",
        )
        cookie = otds.cookie()
        assert cookie is not None
        assert cookie["OTDSTicket"] == "pre-ticket"

    def test_init_with_oauth_token(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            oauth_token="my-oauth-token",
        )
        # Token stored, cookie not set from token
        assert otds.cookie() is None

    def test_init_with_client_credentials(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            client_id="my-client-id",
            client_secret="my-client-secret",
        )
        config = otds.config()
        assert config["clientId"] == "my-client-id"
        assert config["clientSecret"] == "my-client-secret"


class TestOTDSProperties:
    """Tests for OTDS property methods."""

    def test_config_returns_dict(self, otds_instance):
        assert isinstance(otds_instance.config(), dict)

    def test_cookie_none_initially(self, otds_instance):
        assert otds_instance.cookie() is None

    def test_credentials(self, otds_instance):
        creds = otds_instance.credentials()
        assert "userName" in creds
        assert "password" in creds

    def test_client_credentials(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            client_id="cid",
            client_secret="csecret",
        )
        creds = otds.client_credentials()
        assert "client_id" in creds
        assert "client_secret" in creds

    def test_request_header(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
            otds_ticket="test-ticket",
        )
        header = otds.request_header()
        assert "Content-Type" in header
        assert header["Content-Type"] == "application/json"


class TestOTDSAuthenticate:
    """Tests for OTDS.authenticate()."""

    def test_authenticate_password(self, requests_mock):
        requests_mock.post(
            "http://otds.test/otdsws/rest/authentication/credentials",
            json={"ticket": "new-ticket-abc"},
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )
        result = otds.authenticate()

        assert result is not None
        assert "OTDSTicket" in result
        assert result["OTDSTicket"] == "new-ticket-abc"
        assert otds.cookie() is not None

    def test_authenticate_client_credentials(self, requests_mock):
        requests_mock.post(
            "http://otds.test/otdsws/oauth2/token",
            json={"access_token": "client-token-xyz"},
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            client_id="my-client",
            client_secret="my-secret",
        )
        result = otds.authenticate(grant_type="client_credentials")

        assert result is not None

    def test_authenticate_cached(self, requests_mock):
        requests_mock.post(
            "http://otds.test/otdsws/rest/authentication/credentials",
            json={"ticket": "cached-ticket"},
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )
        otds.authenticate()

        # Second call uses cached cookie
        result = otds.authenticate()
        assert result is not None
        assert requests_mock.call_count == 1

    def test_authenticate_revalidate(self, requests_mock):
        requests_mock.post(
            "http://otds.test/otdsws/rest/authentication/credentials",
            json={"ticket": "revalidated-ticket"},
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )
        otds.authenticate()

        # Force revalidation
        result = otds.authenticate(revalidate=True)
        assert result is not None
        assert requests_mock.call_count == 2

    def test_authenticate_no_credentials(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
        )
        result = otds.authenticate()
        assert result is None

    def test_authenticate_connection_error(self, requests_mock):
        requests_mock.post(
            "http://otds.test/otdsws/rest/authentication/credentials",
            exc=requests.ConnectionError("Connection refused"),
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )
        result = otds.authenticate()
        assert result is None

    def test_authenticate_http_error(self, requests_mock):
        requests_mock.post(
            "http://otds.test/otdsws/rest/authentication/credentials",
            status_code=401,
            text="Unauthorized",
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="wrongpassword",
        )
        result = otds.authenticate()
        assert result is None

    def test_authenticate_unsupported_grant_type(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )
        result = otds.authenticate(grant_type="unsupported_type")
        assert result is None


class TestOTDSDoRequest:
    """Tests for OTDS.do_request() method."""

    def test_do_request_success(self, requests_mock):
        # Authenticate first
        requests_mock.post(
            "http://otds.test/otdsws/rest/authentication/credentials",
            json={"ticket": "test-ticket"},
        )
        requests_mock.get(
            "http://otds.test/otdsws/rest/partitions",
            json={"partitions": [{"name": "otds.admin"}]},
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )
        otds.authenticate()

        result = otds.do_request(
            url="http://otds.test/otdsws/rest/partitions",
            method="GET",
        )
        assert result is not None

    def test_do_request_failure(self, requests_mock):
        requests_mock.post(
            "http://otds.test/otdsws/rest/authentication/credentials",
            json={"ticket": "test-ticket"},
        )
        requests_mock.get(
            "http://otds.test/otdsws/rest/fail",
            status_code=500,
            json={"error": "Internal Server Error"},
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )
        otds.authenticate()

        result = otds.do_request(
            url="http://otds.test/otdsws/rest/fail",
            method="GET",
        )
        assert result is None


class TestOTDSParseResponse:
    """Tests for OTDS.parse_request_response()."""

    def test_parse_valid_json(self, requests_mock):
        requests_mock.get(
            "http://test.api/data",
            json={"key": "value"},
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
        )

        import requests as req

        resp = req.get("http://test.api/data")
        result = otds.parse_request_response(resp)
        assert result is not None
        assert result["key"] == "value"

    def test_parse_empty_response(self, requests_mock):
        requests_mock.get(
            "http://test.api/empty",
            text="",
            status_code=200,
        )

        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
        )

        import requests as req

        resp = req.get("http://test.api/empty")
        result = otds.parse_request_response(resp)
        assert result is None


class TestOTDSSetCookie:
    """Tests for OTDS.set_cookie()."""

    def test_set_cookie(self):
        otds = OTDS(
            protocol="http",
            hostname="otds.test",
            port=80,
            username="admin",
            password="secret",
            otds_ticket="initial-ticket",
        )
        result = otds.set_cookie("my-custom-ticket")
        assert result is not None
        assert result["OTDSTicket"] == "my-custom-ticket"
        assert otds.cookie()["OTDSTicket"] == "my-custom-ticket"
