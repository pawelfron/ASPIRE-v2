from unittest.mock import patch

import pytest

from core.lib.measures import nDCG
from core.lib.utils.per_query import (
    difference_summary_column,
    format_number,
    format_query_ids,
    get_per_query_measures,
    per_measure_bar_figure,
    run_style,
    summarize_differences,
)


def test_run_style_cycles_palette():
    color, pattern = run_style(0)
    assert color.startswith("#")
    assert isinstance(pattern, str)
    assert run_style(7)[0] == run_style(0)[0]


def test_format_query_ids_and_numbers():
    assert format_query_ids(["q1", "q2"]) == "q1, q2"
    assert format_query_ids([]) == "-"
    assert format_number(1.2345) == "1.234"
    assert format_number(None) == "-"
    assert format_number(1.2, precision=2) == "1.20"


def test_summarize_differences_classifies_queries():
    summary = summarize_differences(
        [0.8, 0.2, 0.5], [0.5, 0.5, 0.5], ["q1", "q2", "q3"]
    )

    assert summary["improved"] == ["q1"]
    assert summary["degraded"] == ["q2"]
    assert summary["unchanged"] == ["q3"]
    assert summary["total"] == 3
    assert summary["pct_improved"] == pytest.approx(100 / 3)
    assert summary["relative_improvement"] is not None
    assert summary["effect_size"] is not None
    column = difference_summary_column(summary)
    assert column[0] == 1
    assert column[-3] == "q1"


def test_summarize_differences_empty_and_zero_reference():
    empty = summarize_differences([], [], [])
    assert empty["total"] == 0
    assert empty["effect_size"] is None
    assert empty["mean"] == 0.0

    zero_ref = summarize_differences([1.0], [0.0], ["q1"])
    assert zero_ref["relative_improvement"] is None
    assert zero_ref["effect_size"] is None


@patch("core.lib.utils.per_query.get_per_query_measure")
def test_get_per_query_measures_keeps_common_sorted_queries(mock_measure, fake_runs):
    mock_measure.side_effect = [
        {"q10": 0.1, "q2": 0.2, "q1": 0.3},
        {"q2": 0.4, "q1": 0.5, "q9": 0.6},
    ]
    measure = nDCG(cutoff=10, judged_only=False, dcg="log2")
    values, query_ids = get_per_query_measures(fake_runs, [measure])

    assert query_ids == ["q1", "q2"]
    assert set(values["run-a"][measure.measure_name]) == {"q1", "q2"}
    assert values["run-a"][measure.measure_name]["q1"] == 0.3
    assert values["run-b"][measure.measure_name]["q2"] == 0.4


def test_per_measure_bar_figure_adds_grouped_traces_and_zero_line():
    figure = per_measure_bar_figure(
        {
            "nDCG": {"run-a": [0.1, -0.2], "run-b": [0.3, 0.0]},
        },
        ["q1", "q2"],
        "title",
        yaxis_suffix=" difference",
        zero_line=True,
    )
    assert len(figure.data) == 2
    assert figure.layout.title.text == "title"
    assert figure.layout.shapes
