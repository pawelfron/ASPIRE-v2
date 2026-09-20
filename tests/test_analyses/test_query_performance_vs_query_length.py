from unittest.mock import patch

import pandas as pd

from core.lib.analyses.query_performance_vs_query_length import (
    BUCKET_COUNT,
    MINIMUM_QUERIES_FOR_ANOVA,
    QueryPerformanceVsQueryLength,
    QueryPerformanceVsQueryLengthForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.plot import PlotResult
from core.lib.results.table import TableResult
from core.lib.results.value import ValueResult


NDCG = "nDCG(dcg='log2',judged_only=False)@10"


def test_form_prefix():
    form = QueryPerformanceVsQueryLengthForm()
    assert form.prefix == "query_performance_vs_query_length"
    assert form.fields["rolling_window"].initial == 20


def _frame(n: int = 6) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "query_id": [f"q{i}" for i in range(n)],
            "length": list(range(1, n + 1)),
            "performance": [i / n for i in range(n)],
        }
    )


def test_distribution_and_buckets():
    analysis = QueryPerformanceVsQueryLength()
    frame = _frame(8)
    dist = analysis._distribution(frame)
    assert dist.loc["Queries", "Value"] == "8"
    assert dist.loc["Shortest query (tokens)", "Value"] == "1"
    constant = frame.copy()
    constant["length"] = 4
    assert analysis._distribution(constant).loc[
        "Correlation between length and performance", "Value"
    ] == "-"
    width = analysis._equal_width_buckets(frame)
    freq = analysis._equal_frequency_buckets(frame)
    assert width.nunique() <= BUCKET_COUNT
    assert freq.nunique() <= BUCKET_COUNT


def test_anova_requires_enough_queries():
    analysis = QueryPerformanceVsQueryLength()
    assert analysis._anova(_frame(5)) is None
    large = _frame(MINIMUM_QUERIES_FOR_ANOVA)
    verdict = analysis._anova(large)
    assert verdict is not None
    assert "alpha = 0.05" in verdict


def test_scatter_and_bucket_plots():
    analysis = QueryPerformanceVsQueryLength()
    frame = _frame(8)
    scatter = analysis._scatter(frame, "run-a", NDCG, rolling_window=3)
    assert len(scatter.data) == 2
    buckets = analysis._buckets(frame, "run-a", NDCG)
    assert len(buckets.data) == 2


@patch("core.lib.analyses.query_performance_vs_query_length.get_per_query_measures")
@patch("core.lib.analyses.query_performance_vs_query_length.load_queries_file")
def test_execute_reports_unmatched_queries(
    mock_load, mock_measures, fake_task, fake_runs
):
    mock_load.return_value = pd.DataFrame({"query_id": ["other"], "query_text": ["x"]})
    mock_measures.return_value = (
        {"run-a": {NDCG: {"q1": 0.5}}},
        ["q1"],
    )
    result = QueryPerformanceVsQueryLength().execute(
        fake_task, [fake_runs[0]], rolling_window=2
    )
    message = result.children["run-a - query length"]
    assert isinstance(message, ValueResult)
    assert "No query" in message.value


@patch("core.lib.analyses.query_performance_vs_query_length.get_per_query_measures")
@patch("core.lib.analyses.query_performance_vs_query_length.load_queries_file")
def test_execute_builds_plots_and_anova(
    mock_load, mock_measures, fake_task, fake_runs
):
    query_ids = [f"q{i}" for i in range(MINIMUM_QUERIES_FOR_ANOVA)]
    mock_load.return_value = pd.DataFrame(
        {
            "query_id": query_ids,
            "query_text": ["word " * (i + 1) for i in range(MINIMUM_QUERIES_FOR_ANOVA)],
        }
    )
    mock_measures.return_value = (
        {"run-a": {NDCG: {query_id: i / 20 for i, query_id in enumerate(query_ids)}}},
        query_ids,
    )
    result = QueryPerformanceVsQueryLength().execute(
        fake_task, [fake_runs[0]], rolling_window=5
    )
    assert isinstance(result, CompositeResult)
    assert isinstance(
        result.children["run-a - performance vs query length"], PlotResult
    )
    assert isinstance(
        result.children["run-a - performance by length range"], PlotResult
    )
    assert isinstance(
        result.children["run-a - query length distribution"], TableResult
    )
    anova = result.children["run-a - one-way ANOVA across length ranges"]
    assert isinstance(anova, ValueResult)
    assert anova.value.startswith("F =")
