from core.lib.results.composite import CompositeResult
from core.lib.results.value import ValueResult


def test_serialize_nests_children_as_label_payload_pairs():
    payload = CompositeResult(
        {
            "score": ValueResult(3),
            "note": ValueResult("ok"),
        }
    ).serialize()

    assert payload["type"] == "composite"
    assert payload["value"] == [
        ("score", {"type": "value", "value": 3}),
        ("note", {"type": "value", "value": "ok"}),
    ]
