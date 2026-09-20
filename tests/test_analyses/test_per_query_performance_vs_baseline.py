from unittest.mock import patch

from core.lib.analyses.per_query_performance_vs_baseline import (
    PerQueryPerformanceVsBaseline,
    PerQueryPerformanceVsBaselineForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.plot import PlotResult
from core.lib.results.table import TableResult


PREC = "P(rel=1,judged_only=False)@10"
RECALL = "R(rel=1,judged_only=False)@10"


def test_form_populates_baseline_choices(fake_task, fake_runs):
    empty = PerQueryPerformanceVsBaselineForm()
    assert list(dict(empty.fields["baseline_run"].choices)) == [""]
    form = PerQueryPerformanceVsBaselineForm(
        retrieval_task=fake_task, retrieval_runs=fake_runs
    )
    assert form.prefix == "per_query_performance_vs_baseline"
    assert fake_runs[0].id in dict(form.fields["baseline_run"].choices)


@patch("core.lib.analyses.per_query_performance_vs_baseline.get_per_query_measures")
def test_execute_compares_against_selected_baseline(
    mock_measures, fake_task, fake_runs
):
    mock_measures.return_value = (
        {
            "run-a": {
                PREC: {"q1": 0.2, "q2": 0.4},
                RECALL: {"q1": 0.1, "q2": 0.3},
            },
            "run-b": {
                PREC: {"q1": 0.5, "q2": 0.1},
                RECALL: {"q1": 0.4, "q2": 0.2},
            },
        },
        ["q1", "q2"],
    )
    result = PerQueryPerformanceVsBaseline().execute(
        fake_task,
        fake_runs,
        relevance_threshold=1,
        baseline_run=str(fake_runs[0].id),
    )
    assert isinstance(result, CompositeResult)
    assert isinstance(result.children["Per-query difference from baseline"], PlotResult)
    summary_keys = [
        key for key in result.children if key.startswith("Summary vs baseline")
    ]
    assert len(summary_keys) == 2
    assert all(isinstance(result.children[key], TableResult) for key in summary_keys)
