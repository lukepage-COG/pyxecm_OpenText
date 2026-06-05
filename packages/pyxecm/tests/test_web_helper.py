"""Tests for the HTTP helper class."""

from unittest.mock import patch

import pytest
import requests
from pyxecm.helper.web import HTTP


@pytest.fixture
def http():
    return HTTP()


class TestHTTPInit:
    def test_default_init(self, http):
        assert http is not None

    def test_custom_logger(self):
        import logging

        logger = logging.getLogger("test")
        http = HTTP(logger=logger)
        assert http is not None


class TestCheckHostReachable:
    @patch("pyxecm.helper.web.socket.getaddrinfo")
    def test_reachable_host(self, mock_getaddrinfo, http):
        mock_getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 80)),
        ]
        assert http.check_host_reachable("example.com", 80) is True

    @patch("pyxecm.helper.web.socket.getaddrinfo")
    def test_unreachable_host_gaierror(self, mock_getaddrinfo, http):
        import socket

        mock_getaddrinfo.side_effect = socket.gaierror("Name resolution failed")
        assert http.check_host_reachable("nonexistent.invalid", 80) is False

    @patch("pyxecm.helper.web.socket.getaddrinfo")
    def test_unreachable_host_oserror(self, mock_getaddrinfo, http):
        mock_getaddrinfo.side_effect = OSError("Connection error")
        assert http.check_host_reachable("example.com", 80) is False


class TestHTTPRequest:
    def test_get_request(self, http, requests_mock):
        requests_mock.get(
            "https://api.example.com/data",
            json={"key": "value"},
        )
        result = http.http_request(
            "https://api.example.com/data",
            "GET",
        )
        assert result is not None

    def test_post_request(self, http, requests_mock):
        requests_mock.post(
            "https://api.example.com/data",
            json={"created": True},
        )
        result = http.http_request(
            "https://api.example.com/data",
            "POST",
            payload={"name": "test"},
        )
        assert result is not None

    def test_request_connection_error(self, http, requests_mock):
        requests_mock.get(
            "https://api.example.com/data",
            exc=requests.exceptions.ConnectionError("Failed"),
        )
        result = http.http_request(
            "https://api.example.com/data",
            "GET",
        )
        assert result is None


class TestHumanReadableSize:
    def test_bytes(self, http):
        assert http.human_readable_size(500) == "500.00 B"

    def test_kilobytes(self, http):
        assert http.human_readable_size(1024) == "1.00 KB"

    def test_megabytes(self, http):
        assert http.human_readable_size(1048576) == "1.00 MB"

    def test_gigabytes(self, http):
        assert http.human_readable_size(1073741824) == "1.00 GB"

    def test_zero(self, http):
        assert http.human_readable_size(0) == "0.00 B"
