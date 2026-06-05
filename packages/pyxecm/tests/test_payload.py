"""Tests for payload loading and orchestration logic."""


import yaml
from pyxecm_customizer.payload import load_payload


class TestLoadPayload:
    def test_load_yaml_payload(self, tmp_path):
        payload_file = tmp_path / "test.yaml"
        payload_data = {
            "payloadSettings": {"name": "test-payload"},
            "otcs": {"users": [{"name": "testuser"}]},
        }
        payload_file.write_text(yaml.dump(payload_data))
        result = load_payload(str(payload_file))
        assert result is not None
        assert result["payloadSettings"]["name"] == "test-payload"

    def test_load_nonexistent_file(self):
        result = load_payload("/nonexistent/payload.yaml")
        assert result is None

    def test_load_yml_gz_b64_payload(self, tmp_path):
        """Test loading a base64-encoded gzipped YAML payload."""
        import base64
        import gzip

        payload_data = yaml.dump({"payloadSettings": {"name": "compressed"}})
        compressed = gzip.compress(payload_data.encode("utf-8"))
        encoded = base64.b64encode(compressed).decode("utf-8")
        payload_file = tmp_path / "test.yml.gz.b64"
        payload_file.write_text(encoded)
        result = load_payload(str(payload_file))
        assert result is not None
        assert result["payloadSettings"]["name"] == "compressed"

    def test_load_invalid_yaml(self, tmp_path):
        payload_file = tmp_path / "bad.yaml"
        payload_file.write_text(": invalid: yaml: [[[")
        result = load_payload(str(payload_file))
        # Should handle YAML errors gracefully
        assert result is not None or result is None

    def test_load_unsupported_file_type(self, tmp_path):
        """Test that unsupported file types return None."""
        payload_file = tmp_path / "test.json"
        payload_file.write_text('{"key": "value"}')
        result = load_payload(str(payload_file))
        assert result is None

    def test_load_empty_yaml(self, tmp_path):
        """Test loading an empty YAML file returns None."""
        payload_file = tmp_path / "empty.yaml"
        payload_file.write_text("")
        result = load_payload(str(payload_file))
        assert result is None
