"""Unit tests for pyxecm.helper.web module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from pyxecm.helper.web import REQUEST_FORM_HEADERS


class TestHTTPCheckHostReachable:
    """Tests for HTTP.check_host_reachable()."""

    def test_reachable_host(self, http_client, requests_mock):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 80))]):
            assert http_client.check_host_reachable("localhost", 80) is True

    def test_unreachable_host_gaierror(self, http_client):
        import socket

        with patch("socket.getaddrinfo", side_effect=socket.gaierror(8, "Name not resolved")):
            assert http_client.check_host_reachable("nonexistent.test", 80) is False

    def test_unreachable_host_oserror(self, http_client):
        with patch("socket.getaddrinfo", side_effect=OSError(111, "Connection refused")):
            assert http_client.check_host_reachable("localhost", 9999) is False


class TestHTTPRequest:
    """Tests for HTTP.http_request()."""

    def test_get_request_success(self, http_client, requests_mock):
        requests_mock.get("http://test.api/data", json={"key": "value"}, status_code=200)

        response = http_client.http_request("http://test.api/data", method="GET")

        assert response is not None
        assert response.ok
        assert response.json() == {"key": "value"}

    def test_post_request_success(self, http_client, requests_mock):
        requests_mock.post("http://test.api/submit", json={"ok": True}, status_code=200)

        response = http_client.http_request(
            "http://test.api/submit",
            method="POST",
            payload={"field": "value"},
        )

        assert response is not None
        assert response.ok

    def test_put_request_success(self, http_client, requests_mock):
        requests_mock.put("http://test.api/update", json={"ok": True}, status_code=200)

        response = http_client.http_request(
            "http://test.api/update",
            method="PUT",
            payload={"field": "new_value"},
        )

        assert response is not None
        assert response.ok

    def test_delete_request_success(self, http_client, requests_mock):
        requests_mock.delete("http://test.api/remove", json={"ok": True}, status_code=200)

        response = http_client.http_request("http://test.api/remove", method="DELETE")

        assert response is not None
        assert response.ok

    def test_patch_request_success(self, http_client, requests_mock):
        requests_mock.patch("http://test.api/patch", json={"ok": True}, status_code=200)

        response = http_client.http_request("http://test.api/patch", method="PATCH")

        assert response is not None
        assert response.ok

    def test_http_error_status_returns_none(self, http_client, requests_mock):
        requests_mock.get("http://test.api/fail", status_code=500, text="Server Error")

        response = http_client.http_request(
            "http://test.api/fail",
            method="GET",
            retries=0,
        )

        assert response is None

    def test_connection_error_returns_none(self, http_client, requests_mock):
        requests_mock.get("http://test.api/err", exc=requests.ConnectionError("Refused"))

        response = http_client.http_request(
            "http://test.api/err",
            method="GET",
            retries=0,
        )

        assert response is None

    def test_timeout_error_returns_none(self, http_client, requests_mock):
        requests_mock.get("http://test.api/timeout", exc=requests.Timeout("Timed out"))

        response = http_client.http_request(
            "http://test.api/timeout",
            method="GET",
            retries=0,
        )

        assert response is None

    def test_retries_on_failure(self, http_client, requests_mock):
        requests_mock.get(
            "http://test.api/retry",
            [
                {"status_code": 503, "text": "Unavailable"},
                {"json": {"ok": True}, "status_code": 200},
            ],
        )

        response = http_client.http_request(
            "http://test.api/retry",
            method="GET",
            retries=1,
            wait_time=0.0,
        )

        assert response is not None
        assert response.ok

    def test_default_headers_used(self, http_client, requests_mock):
        requests_mock.get("http://test.api/data", json={}, status_code=200)

        http_client.http_request("http://test.api/data", method="GET")

        assert requests_mock.last_request.headers["Content-Type"] == REQUEST_FORM_HEADERS["Content-Type"]

    def test_custom_headers(self, http_client, requests_mock):
        requests_mock.get("http://test.api/data", json={}, status_code=200)

        custom_headers = {"Authorization": "Bearer token123", "Content-Type": "application/json"}
        http_client.http_request("http://test.api/data", method="GET", headers=custom_headers)

        assert requests_mock.last_request.headers["Authorization"] == "Bearer token123"


class TestDownloadFile:
    """Tests for HTTP.download_file()."""

    def test_download_success(self, http_client, requests_mock):
        content = b"file content here"
        requests_mock.get("http://test.api/file.txt", content=content, status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = str(Path(tmpdir) / "file.txt")
            result = http_client.download_file("http://test.api/file.txt", filepath)

            assert result is True
            assert Path(filepath).exists()
            assert Path(filepath).read_bytes() == content

    def test_download_creates_directory(self, http_client, requests_mock):
        requests_mock.get("http://test.api/file.txt", content=b"data", status_code=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = str(Path(tmpdir) / "subdir" / "file.txt")
            result = http_client.download_file("http://test.api/file.txt", filepath)

            assert result is True
            assert Path(filepath).exists()

    def test_download_invalid_url(self, http_client):
        result = http_client.download_file("not-a-url", "/tmp/file.txt")
        assert result is False

    def test_download_failed_request(self, http_client, requests_mock):
        requests_mock.get("http://test.api/missing", status_code=404)

        result = http_client.download_file("http://test.api/missing", "/tmp/file.txt")
        assert result is False


class TestHumanReadableSize:
    """Tests for HTTP.human_readable_size()."""

    @pytest.mark.parametrize(
        ("size", "expected"),
        [
            (0, "0.00 B"),
            (512, "512.00 B"),
            (1024, "1.00 KB"),
            (1048576, "1.00 MB"),
            (1073741824, "1.00 GB"),
            (1099511627776, "1.00 TB"),
        ],
    )
    def test_human_readable_size(self, http_client, size, expected):
        assert http_client.human_readable_size(size) == expected


class TestExtractContent:
    """Tests for HTTP.extract_content()."""

    def test_extract_content_success(self, http_client, requests_mock):
        html_content = '<html><body><div class="content">Hello World</div></body></html>'
        requests_mock.get("http://test.api/page", text=html_content, status_code=200)

        result = http_client.extract_content("http://test.api/page", '//div[@class="content"]')

        assert result == "Hello World"

    def test_extract_content_no_match(self, http_client, requests_mock):
        html_content = "<html><body><p>No match here</p></body></html>"
        requests_mock.get("http://test.api/page", text=html_content, status_code=200)

        result = http_client.extract_content("http://test.api/page", '//div[@class="missing"]')

        assert result == ""
