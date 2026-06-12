"""Tests for the HTTP helper class."""

import requests
import requests_mock as rm
from pyxecm.helper.web import HTTP, REQUEST_MAX_RETRIES, REQUEST_TIMEOUT


class TestHTTPCheckHostReachable:
    def test_reachable_host(self, http_client, monkeypatch):
        monkeypatch.setattr(
            "socket.getaddrinfo",
            lambda *a, **kw: [(2, 1, 6, "", ("127.0.0.1", 80))],
        )
        assert http_client.check_host_reachable("localhost", 80) is True

    def test_unreachable_host(self, http_client, monkeypatch):
        import socket

        def raise_gaierror(*a, **kw):
            raise socket.gaierror("Name or service not known")

        monkeypatch.setattr("socket.getaddrinfo", raise_gaierror)
        assert http_client.check_host_reachable("nonexistent.invalid") is False

    def test_connection_error(self, http_client, monkeypatch):
        def raise_oserror(*a, **kw):
            raise OSError("Connection refused")

        monkeypatch.setattr("socket.getaddrinfo", raise_oserror)
        assert http_client.check_host_reachable("localhost", 9999) is False


class TestHTTPRequest:
    def test_successful_get(self, http_client):
        with rm.Mocker() as m:
            m.get("http://example.com/api", text='{"ok": true}', status_code=200)
            response = http_client.http_request("http://example.com/api", method="GET")
            assert response is not None
            assert response.ok
            assert response.status_code == 200

    def test_successful_post(self, http_client):
        with rm.Mocker() as m:
            m.post("http://example.com/api", json={"created": True}, status_code=201)
            response = http_client.http_request(
                "http://example.com/api",
                method="POST",
                payload={"key": "value"},
            )
            assert response is not None
            assert response.status_code == 201

    def test_successful_put(self, http_client):
        with rm.Mocker() as m:
            m.put("http://example.com/api/1", json={"updated": True})
            response = http_client.http_request("http://example.com/api/1", method="PUT")
            assert response is not None
            assert response.ok

    def test_successful_patch(self, http_client):
        with rm.Mocker() as m:
            m.patch("http://example.com/api/1", json={"patched": True})
            response = http_client.http_request("http://example.com/api/1", method="PATCH")
            assert response is not None
            assert response.ok

    def test_successful_delete(self, http_client):
        with rm.Mocker() as m:
            m.delete("http://example.com/api/1", status_code=204)
            response = http_client.http_request("http://example.com/api/1", method="DELETE")
            assert response is not None
            assert response.status_code == 204

    def test_error_4xx(self, http_client):
        with rm.Mocker() as m:
            m.get(
                "http://example.com/api",
                status_code=404,
                headers={"content-type": "application/json"},
                json={"error": "Not Found"},
            )
            response = http_client.http_request(
                "http://example.com/api",
                method="GET",
                retries=0,
            )
            assert response is None

    def test_error_5xx(self, http_client):
        with rm.Mocker() as m:
            m.get(
                "http://example.com/api",
                status_code=500,
                headers={"content-type": "application/json"},
                json={"error": "Internal Server Error"},
            )
            response = http_client.http_request(
                "http://example.com/api",
                method="GET",
                retries=0,
            )
            assert response is None

    def test_connection_error_returns_none(self, http_client):
        with rm.Mocker() as m:
            m.get("http://example.com/api", exc=requests.ConnectionError)
            response = http_client.http_request(
                "http://example.com/api",
                method="GET",
                retries=0,
            )
            assert response is None

    def test_timeout_returns_none(self, http_client):
        with rm.Mocker() as m:
            m.get("http://example.com/api", exc=requests.Timeout)
            response = http_client.http_request(
                "http://example.com/api",
                method="GET",
                retries=0,
            )
            assert response is None

    def test_retry_on_failure(self, http_client):
        with rm.Mocker() as m:
            m.get(
                "http://example.com/api",
                [
                    {"status_code": 503, "headers": {"content-type": "application/json"}, "json": {}},
                    {"status_code": 200, "json": {"ok": True}},
                ],
            )
            response = http_client.http_request(
                "http://example.com/api",
                method="GET",
                retries=1,
                wait_time=0.0,
            )
            assert response is not None
            assert response.ok

    def test_stream_mode(self, http_client):
        with rm.Mocker() as m:
            m.get("http://example.com/file", content=b"file-content", status_code=200)
            response = http_client.http_request(
                "http://example.com/file",
                method="GET",
                stream=True,
            )
            assert response is not None
            assert response.ok

    def test_wait_on_status(self, http_client):
        with rm.Mocker() as m:
            m.get(
                "http://example.com/api",
                [
                    {"status_code": 200, "json": {"status": "pending"}},
                    {"status_code": 200, "json": {"status": "done"}},
                ],
            )
            response = http_client.http_request(
                "http://example.com/api",
                method="GET",
                retries=1,
                wait_time=0.0,
                wait_on_status=[200],
            )
            # With wait_on_status=[200], the first 200 triggers a retry
            # The second 200 also triggers a retry, then retries exhausted -> None
            assert response is None


class TestDownloadFile:
    def test_successful_download(self, http_client, tmp_path):
        target = str(tmp_path / "subdir" / "test.txt")
        with rm.Mocker() as m:
            m.get("http://example.com/file.txt", content=b"hello world")
            result = http_client.download_file(
                url="http://example.com/file.txt",
                filename=target,
            )
            assert result is True
            with open(target, "rb") as f:
                assert f.read() == b"hello world"

    def test_invalid_url(self, http_client, tmp_path):
        result = http_client.download_file(
            url="not-a-url",
            filename=str(tmp_path / "test.txt"),
        )
        assert result is False

    def test_failed_request(self, http_client, tmp_path):
        with rm.Mocker() as m:
            m.get("http://example.com/file.txt", status_code=404, headers={"content-type": "application/json"})
            result = http_client.download_file(
                url="http://example.com/file.txt",
                filename=str(tmp_path / "test.txt"),
                retries=0,
            )
            assert result is False


class TestHumanReadableSize:
    def test_bytes(self, http_client):
        assert http_client.human_readable_size(500) == "500.00 B"

    def test_kilobytes(self, http_client):
        assert http_client.human_readable_size(2048) == "2.00 KB"

    def test_megabytes(self, http_client):
        assert http_client.human_readable_size(1048576) == "1.00 MB"

    def test_gigabytes(self, http_client):
        assert http_client.human_readable_size(1073741824) == "1.00 GB"


class TestExtractContent:
    def test_successful_extraction(self, http_client):
        html_content = "<html><body><div id='test'>Hello World</div></body></html>"
        with rm.Mocker() as m:
            m.get("http://example.com", text=html_content, status_code=200)
            result = http_client.extract_content("http://example.com", "//div[@id='test']")
            assert result == "Hello World"

    def test_failed_request(self, http_client):
        with rm.Mocker() as m:
            m.get("http://example.com", exc=requests.ConnectionError)
            # extract_content doesn't guard against None from http_request
            import pytest

            with pytest.raises(AttributeError):
                http_client.extract_content("http://example.com", "//div")
