from unittest.mock import patch

from core.lib.analyses.per_query_performance import (
    PerQueryPerformance,
    PerQueryPerformanceForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.plot import PlotResult
from core.lib.results.table import TableResult
from tests.fakes import make_binary_qrels_dataframe, make_fake_task


NDCG = "nDCG(dcg='log2',judged_only=False)@10"
PREC = "P(rel=1,judged_only=False)@10"


def test_form_uses_relevance_threshold(fake_task, fake_runs):
    form = PerQueryPerformanceForm(retrieval_task=fake_task, retrieval_runs=fake_runs)
    assert form.prefix == "per_query_performance"
    assert form.fields["relevance_threshold"].initial == 1
    binary = PerQueryPerformanceForm(
        retrieval_task=make_fake_task(qrels=make_binary_qrels_dataframe()),
        retrieval_runs=fake_runs,
    )
    assert binary.fields["relevance_threshold"].disabled is True


def test_compare_runs_finds_equal_and_large_gaps():
    equal, gaps, threshold = PerQueryPerformance()._compare_runs(
        {"run-a": [0.5, 0.1, 0.4], "run-b": [0.5, 0.9, 0.41]},
        ["q1", "q2", "q3"],
    )
    assert equal == ["q1"]
    assert threshold > 0
    gap_ids = [query_id for query_id, _, _ in gaps]
    assert "q2" in gap_ids
    assert "q3" not in gap_ids


def test_compare_runs_empty_values():
    equal, gaps, threshold = PerQueryPerformance()._compare_runs({}, [])
    assert equal == []
    assert gaps == []
    assert threshold == 0.0


@patch("core.lib.analyses.per_query_performance.get_per_query_measures")
def test_execute_single_run_skips_consistency(mock_measures, fake_task, fake_runs):
    mock_measures.return_value = (
        {
            "run-a": {
                NDCG: {"q1": 0.5, "q2": 0.4},
                PREC: {"q1": 0.3, "q2": 0.2},
            }
        },
        ["q1", "q2"],
    )
    result = PerQueryPerformance().execute(
        fake_task, [fake_runs[0]], relevance_threshold=1
    )
    assert isinstance(result, CompositeResult)
    assert isinstance(result.children["Per-query performance"], PlotResult)
    assert "Cross-experiment consistency" not in result.children


@patch("core.lib.analyses.per_query_performance.get_per_query_measures")
def test_execute_multiple_runs_adds_gap_tables(mock_measures, fake_task, fake_runs):
    mock_measures.return_value = (
        {
            "run-a": {
                NDCG: {"q1": 0.1, "q2": 0.5},
                PREC: {"q1": 0.1, "q2": 0.5},
            },
            "run-b": {
                NDCG: {"q1": 0.9, "q2": 0.5},
                PREC: {"q1": 0.9, "q2": 0.5},
            },
        },
        ["q1", "q2"],
    )
    result = PerQueryPerformance().execute(fake_task, fake_runs, relevance_threshold=1)
    assert "Cross-experiment consistency" in result.children
    assert isinstance(result.children["Cross-experiment consistency"], TableResult)
    assert any(key.startswith("Large performance gaps") for key in result.children)
