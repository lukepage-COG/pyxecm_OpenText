"""Shared fixtures for pyxecm tests."""

import logging

import pytest
import requests_mock as rm
from pyxecm.helper.web import HTTP
from pyxecm.otcs import OTCS
from pyxecm.otds import OTDS


@pytest.fixture
def requests_mock():
    """Provide a requests-mock adapter for HTTP mocking."""
    with rm.Mocker() as m:
        yield m


@pytest.fixture
def http_client():
    """Provide an HTTP helper instance."""
    return HTTP(logger=logging.getLogger("test.http"))


@pytest.fixture
def otcs_instance(requests_mock):
    """Create an OTCS instance with mocked authentication."""
    requests_mock.post(
        "http://otcs.test:8080/cs/cs/api/v1/auth",
        json={"ticket": "test-ticket-123"},
    )

    otcs = OTCS(
        protocol="http",
        hostname="otcs.test",
        port=8080,
        username="admin",
        password="secret",
    )
    return otcs


@pytest.fixture
def authenticated_otcs(requests_mock):
    """Create an authenticated OTCS instance."""
    requests_mock.post(
        "http://otcs.test:8080/cs/cs/api/v1/auth",
        json={"ticket": "test-ticket-123"},
    )

    otcs = OTCS(
        protocol="http",
        hostname="otcs.test",
        port=8080,
        username="admin",
        password="secret",
    )
    otcs.authenticate()
    return otcs


@pytest.fixture
def otds_instance():
    """Create an OTDS instance."""
    return OTDS(
        protocol="http",
        hostname="otds.test",
        port=80,
        username="admin",
        password="secret",
    )


@pytest.fixture
def authenticated_otds(requests_mock):
    """Create an authenticated OTDS instance."""
    requests_mock.post(
        "http://otds.test/otdsws/rest/authentication/credentials",
        json={"ticket": "otds-ticket-abc"},
    )

    otds = OTDS(
        protocol="http",
        hostname="otds.test",
        port=80,
        username="admin",
        password="secret",
    )
    otds.authenticate()
    return otds


@pytest.fixture
def success_response():
    """Standard success dict pattern used by OTCS/OTDS responses."""
    return {
        "ok": True,
        "status_code": 200,
        "results": {},
    }


@pytest.fixture
def error_response():
    """Standard error dict pattern."""
    return {
        "ok": False,
        "status_code": 500,
        "error": "Internal Server Error",
    }
