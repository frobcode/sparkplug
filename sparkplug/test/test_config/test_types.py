from sparkplug.config.types import parse_bool


def test_parse_bool():
    value_to_result = (
        (False, False),
        ("False", False),
        ("false", False),
        ("F", False),
        ("0", False),
        ("No", False),
        (True, True),
        ("True", True),
        ("true", True),
        ("T", True),
        ("1", True),
        ("Yes", True),
    )

    for value, result in value_to_result:
        assert parse_bool(value) == result


def test_parse_bool_raises_error():
    for value in ("definitely yes", "noooo"):
        try:
            parse_bool(value)
            assert False
        except ValueError:
            assert True
