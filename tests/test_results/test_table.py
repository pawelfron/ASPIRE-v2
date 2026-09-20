import pandas as pd

from core.lib.results.table import TableResult


def test_serialize_includes_data_with_index():
    frame = pd.DataFrame({"a": [1, 2], "b": [3, 4]}, index=["x", "y"])
    payload = TableResult(frame).serialize()

    assert payload["type"] == "table"
    assert payload["value"]["index"] == ["x", "y"]
    assert payload["value"]["columns"] == ["a", "b"]
    assert payload["value"]["data"] == [[1, 3], [2, 4]]
    assert payload["value"]["data_with_index"] == [["x", 1, 3], ["y", 2, 4]]
