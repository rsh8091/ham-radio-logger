import pytest

from hamqth_api import _parse_xml, HamQTHError


def test_parse_xml_success():
    xml_text = "<root><child>value</child></root>"

    root = _parse_xml(xml_text)

    assert root.tag == "root"
    assert root.find("child").text == "value"


def test_parse_xml_invalid_xml():
    bad_xml = "<root><child></root>"

    with pytest.raises(HamQTHError) as exc:
        _parse_xml(bad_xml)

    assert "XML" in str(exc.value)
