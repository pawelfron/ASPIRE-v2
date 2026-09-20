from unittest.mock import patch

import pytest

from core.lib.analyses.experimental_evaluation import (
    ExperimentalEvaluation,
    ExperimentalEvaluationForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.table import TableResult


def test_form_populates_baseline_choices(fake_task, fake_runs):
    empty = ExperimentalEvaluationForm()
    assert list(dict(empty.fields["baseline_run"].choices)) == [""]
    form = ExperimentalEvaluationForm(
        retrieval_task=fake_task, retrieval_runs=fake_runs
    )
    assert form.prefix == "experimental_evaluation"
    choices = dict(form.fields["baseline_run"].choices)
    assert fake_runs[0].id in choices
    assert choices[fake_runs[0].id] == "run-a"


@patch("core.lib.analyses.experimental_evaluation.get_per_query_measure")
def test_execute_returns_measure_and_p_value_tables(mock_measure, fake_task, fake_runs):
    def per_query(run, measure):
        if run.title == "run-a":
            return {"q1": 0.2, "q2": 0.4}
        return {"q1": 0.8, "q2": 0.9}

    mock_measure.side_effect = per_query
    result = ExperimentalEvaluation().execute(
        fake_task,
        fake_runs,
        relevance_threshold=1,
        correction_method="bonferroni",
        correction_value=0.05,
        baseline_run=str(fake_runs[0].id),
    )
    assert isinstance(result, CompositeResult)
    assert set(result.children) == {
        "Measure values",
        "P-values",
        "Corrected P-values",
    }
    measures = result.children["Measure values"]
    assert isinstance(measures, TableResult)
    assert "run-a" in measures.dataframe.columns
    assert measures.dataframe.loc[:, "run-a"].iloc[0] == pytest.approx(0.3)
    pvalues = result.children["P-values"].dataframe
    assert "run-b" in pvalues.columns
    assert "run-a" not in pvalues.columns
