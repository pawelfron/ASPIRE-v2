from core.lib.results.value import ValueResult


def test_serialize_scalar():
    assert ValueResult(3).serialize() == {"type": "value", "value": 3}


def test_serialize_string():
    assert ValueResult("ok").serialize() == {"type": "value", "value": "ok"}
