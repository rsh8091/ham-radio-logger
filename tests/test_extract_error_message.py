from hamqth_api import _extract_error_message, _parse_xml


def test_extract_error_message_has_error_message():
    test_string = "<HamQTH><session><error>...  </error></session></HamQTH>"
    error_xml = _parse_xml(test_string)
    error_message = _extract_error_message(error_xml)
    assert error_message == "..."


def test_extract_error_message_no_error_tag():
    test_string = "<HamQTH><session></session></HamQTH>"
    error_xml = _parse_xml(test_string)
    error_message = _extract_error_message(error_xml)
    assert error_message == None


def test_extract_error_message_no_error_message():
    test_string = "<HamQTH><session><error></error></session></HamQTH>"
    error_xml = _parse_xml(test_string)
    error_message = _extract_error_message(error_xml)
    assert error_message == None
