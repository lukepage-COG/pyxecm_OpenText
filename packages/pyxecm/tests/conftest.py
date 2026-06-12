"""Shared test fixtures for pyxecm tests."""

import logging

import pytest
import requests_mock as rm

from pyxecm.helper.web import HTTP
from pyxecm.otcs import OTCS
from pyxecm.otds import OTDS


@pytest.fixture
def http_client():
    return HTTP(logger=logging.getLogger("test"))


@pytest.fixture
def mock_adapter():
    with rm.Mocker() as m:
        yield m


@pytest.fixture
def otcs(mock_adapter):
    mock_adapter.post(
        "http://otcs:8080/cs/cs/api/v1/auth",
        json={"ticket": "test-ticket-123"},
    )
    mock_adapter.get(
        "http://otcs:8080/cs/cs/api/v1/serverinfo",
        json={"results": {"data": {"server": {"version": "24.4"}}}},
    )
    return OTCS(
        protocol="http",
        hostname="otcs",
        port=8080,
        username="admin",
        password="password",
    )


@pytest.fixture
def otds(mock_adapter):
    mock_adapter.post(
        "http://otds:80/otdsws/rest/authentication/credentials",
        json={"ticket": "otds-ticket-123", "token": "otds-token-456"},
    )
    return OTDS(
        protocol="http",
        hostname="otds",
        port=80,
        username="admin",
        password="password",
    )
