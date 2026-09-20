from unittest.mock import patch

from core.lib.analyses.per_query_performance_vs_threshold import (
    PerQueryPerformanceVsThreshold,
    PerQueryPerformanceVsThresholdForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.plot import PlotResult
from core.lib.results.table import TableResult
from core.lib.results.value import ValueResult


NDCG = "nDCG(dcg='log2',judged_only=False)@10"


def test_form_prefix():
    form = PerQueryPerformanceVsThresholdForm()
    assert form.prefix == "per_query_performance_vs_threshold"
    assert form.fields["threshold"].initial == 0.0


def test_median_of_others():
    values = {
        "run-a": {NDCG: {"q1": 0.2, "q2": 0.8}},
        "run-b": {NDCG: {"q1": 0.4, "q2": 0.6}},
        "run-c": {NDCG: {"q1": 1.0, "q2": 0.0}},
    }
    medians = PerQueryPerformanceVsThreshold()._median_of_others(
        values, ["run-a", "run-b", "run-c"], "run-a", NDCG, ["q1", "q2"]
    )
    assert medians == [0.7, 0.3]


@patch("core.lib.analyses.per_query_performance_vs_threshold.get_per_query_measures")
def test_threshold_zero_requires_two_runs(mock_measures, fake_task, fake_runs):
    mock_measures.return_value = (
        {"run-a": {NDCG: {"q1": 0.5}}},
        ["q1"],
    )
    result = PerQueryPerformanceVsThreshold().execute(
        fake_task, [fake_runs[0]], threshold=0.0
    )
    message = result.children["Median comparison"]
    assert isinstance(message, ValueResult)
    assert "at least two" in message.value


@patch("core.lib.analyses.per_query_performance_vs_threshold.get_per_query_measures")
def test_threshold_zero_compares_to_median(mock_measures, fake_task, fake_runs):
    mock_measures.return_value = (
        {
            "run-a": {NDCG: {"q1": 0.2, "q2": 0.8}},
            "run-b": {NDCG: {"q1": 0.4, "q2": 0.6}},
        },
        ["q1", "q2"],
    )
    result = PerQueryPerformanceVsThreshold().execute(
        fake_task, fake_runs, threshold=0.0
    )
    assert any(key.startswith("Median comparison -") for key in result.children)
    assert any(key.startswith("Summary vs median") for key in result.children)
    assert isinstance(
        result.children["Median comparison - run-a"], PlotResult
    )


@patch("core.lib.analyses.per_query_performance_vs_threshold.get_per_query_measures")
def test_nonzero_threshold_plots_differences(mock_measures, fake_task, fake_runs):
    mock_measures.return_value = (
        {
            "run-a": {NDCG: {"q1": 0.8, "q2": 0.2}},
            "run-b": {NDCG: {"q1": 0.4, "q2": 0.6}},
        },
        ["q1", "q2"],
    )
    result = PerQueryPerformanceVsThreshold().execute(
        fake_task, fake_runs, threshold=0.5
    )
    assert isinstance(result, CompositeResult)
    assert isinstance(
        result.children["Per-query difference from threshold"], PlotResult
    )
    assert any(key.startswith("Summary vs threshold") for key in result.children)
    assert isinstance(
        result.children["Summary vs threshold - " + NDCG], TableResult
    )
