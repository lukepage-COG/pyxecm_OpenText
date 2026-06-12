"""Tests for the Customizer Payload module."""

import yaml
from pyxecm_customizer.payload import load_payload


class TestLoadPayload:
    def test_load_yaml_payload(self, tmp_path):
        payload_file = tmp_path / "test.yaml"
        data = {"key": "value", "nested": {"a": 1}}
        payload_file.write_text(yaml.dump(data))
        result = load_payload(str(payload_file))
        assert result is not None
        assert result["key"] == "value"

    def test_load_unsupported_format_returns_none(self, tmp_path):
        payload_file = tmp_path / "test.json"
        payload_file.write_text('{"key": "value"}')
        result = load_payload(str(payload_file))
        assert result is None

    def test_load_nonexistent_file(self):
        result = load_payload("/nonexistent/path/file.yaml")
        assert result is None

    def test_load_invalid_format(self, tmp_path):
        payload_file = tmp_path / "test.txt"
        payload_file.write_text("not yaml or json")
        result = load_payload(str(payload_file))
        assert result is None
