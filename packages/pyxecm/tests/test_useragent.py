"""Tests for the shared USER_AGENT helper."""

from pyxecm.helper.useragent import build_user_agent


class TestBuildUserAgent:
    def test_returns_string(self):
        result = build_user_agent("pyxecm.otcs")
        assert isinstance(result, str)

    def test_contains_module_name(self):
        result = build_user_agent("pyxecm.otcs")
        assert "pyxecm.otcs" in result

    def test_contains_python_version(self):
        result = build_user_agent("pyxecm.test")
        assert "Python/" in result

    def test_contains_app_name(self):
        result = build_user_agent("pyxecm.test")
        assert "pyxecm/" in result

    def test_contains_requests_version(self):
        result = build_user_agent("pyxecm.test")
        assert "Requests/" in result

    def test_different_modules(self):
        ua1 = build_user_agent("pyxecm.otcs")
        ua2 = build_user_agent("pyxecm.otds")
        assert ua1 != ua2
        assert "pyxecm.otcs" in ua1
        assert "pyxecm.otds" in ua2
