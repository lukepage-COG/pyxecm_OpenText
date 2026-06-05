"""Shared pytest fixtures for pyxecm tests."""

import pytest
import requests_mock as rm


@pytest.fixture
def mock_otcs_config():
    """Return a minimal configuration dict for OTCS tests."""
    return {
        "protocol": "https",
        "hostname": "otcs.example.com",
        "port": 443,
        "username": "admin",
        "password": "secret",
    }


@pytest.fixture
def mock_otds_config():
    """Return a minimal configuration dict for OTDS tests."""
    return {
        "protocol": "https",
        "hostname": "otds.example.com",
        "port": 443,
        "username": "admin",
        "password": "secret",
    }


@pytest.fixture
def requests_mock():
    """Provide a requests_mock adapter for HTTP mocking."""
    with rm.Mocker() as m:
        yield m


@pytest.fixture
def otcs_base_url():
    """Return the base URL for OTCS API calls."""
    return "https://otcs.example.com:443"


@pytest.fixture
def otds_base_url():
    """Return the base URL for OTDS API calls."""
    return "https://otds.example.com:443"
