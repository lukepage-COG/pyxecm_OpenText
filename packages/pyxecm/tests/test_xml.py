"""Tests for the XML helper class."""

from pyxecm.helper.xml import XML


class TestRemoveXMLNamespace:
    def test_with_namespace(self):
        assert XML.remove_xml_namespace("{http://example.com}element") == "element"

    def test_without_namespace(self):
        assert XML.remove_xml_namespace("element") == "element"

    def test_empty_string(self):
        assert XML.remove_xml_namespace("") == ""


class TestXMLToDict:
    def test_simple_xml(self):
        xml_str = "<root><name>Test</name><value>42</value></root>"
        result = XML.xml_to_dict(xml_str)
        assert isinstance(result, dict)
        assert "root" in result

    def test_nested_xml(self):
        xml_str = "<root><parent><child>value</child></parent></root>"
        result = XML.xml_to_dict(xml_str)
        assert "root" in result

    def test_with_namespace(self):
        xml_str = '<root xmlns:ns="http://example.com"><ns:item>value</ns:item></root>'
        result = XML.xml_to_dict(xml_str)
        assert isinstance(result, dict)

    def test_with_encoding(self):
        xml_str = "<root><name>Test</name></root>"
        result = XML.xml_to_dict(xml_str, encode=True)
        assert isinstance(result, dict)

    def test_with_attributes(self):
        xml_str = '<root attr="val"><item>text</item></root>'
        result = XML.xml_to_dict(xml_str, include_attributes=True)
        assert isinstance(result, dict)
