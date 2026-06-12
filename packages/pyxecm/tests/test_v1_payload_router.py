"""Tests for v1_payload router functions."""

from pyxecm_api.v1_payload.functions import prepare_dependencies


class TestPrepareDependencies:
    def test_comma_separated_string(self):
        result = prepare_dependencies(["1,2,3"])
        assert result == [1, 2, 3]

    def test_single_value(self):
        result = prepare_dependencies(["42"])
        assert result == [42]

    def test_empty_list(self):
        result = prepare_dependencies([])
        assert result is None

    def test_negative_one_marker(self):
        result = prepare_dependencies(["-1"])
        assert result == [-1]

    def test_with_spaces(self):
        result = prepare_dependencies(["1, 2, 3"])
        assert result == [1, 2, 3]
