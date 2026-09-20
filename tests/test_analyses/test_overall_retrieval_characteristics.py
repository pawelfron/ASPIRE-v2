from unittest.mock import patch

from core.lib.analyses.overall_retrieval_characteristics import (
    OverallRetrievalCharacteristics,
    OverallRetrievalCharacteristicsForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.table import TableResult
from tests.fakes import make_binary_qrels_dataframe, make_fake_task


def test_form_without_task_keeps_unbounded_threshold():
    form = OverallRetrievalCharacteristicsForm()
    assert form.fields["relevance_threshold"].disabled is False
    assert form.fields["relevance_threshold"].initial is None


def test_form_prefix_and_threshold_from_qrels(fake_task, fake_runs):
    form = OverallRetrievalCharacteristicsForm(
        retrieval_task=fake_task, retrieval_runs=fake_runs
    )
    assert form.prefix == "overall_retrieval_characteristics"
    field = form.fields["relevance_threshold"]
    assert field.initial == 2
    assert field.max_value == 2
    assert field.disabled is False


def test_form_disables_threshold_when_binary(fake_runs):
    task = make_fake_task(qrels=make_binary_qrels_dataframe())
    form = OverallRetrievalCharacteristicsForm(
        retrieval_task=task, retrieval_runs=fake_runs
    )
    assert form.fields["relevance_threshold"].disabled is True


@patch(
    "core.lib.analyses.overall_retrieval_characteristics.get_aggregate_measure",
    side_effect=lambda run, measure: {"run-a": 1.0, "run-b": 2.0}[run.title],
)
def test_execute_builds_measure_table(_mock_measure, fake_task, fake_runs):
    result = OverallRetrievalCharacteristics().execute(
        fake_task, fake_runs, relevance_threshold=1
    )
    assert isinstance(result, CompositeResult)
    assert set(result.children) == {
        "Overall measures",
        "Precision measures",
        "Recall measures",
    }
    overall = result.children["Overall measures"]
    assert isinstance(overall, TableResult)
    assert list(overall.dataframe.columns) == ["run-a", "run-b"]
    assert "NumQ" in overall.dataframe.index
    assert overall.dataframe.loc["NumQ", "run-a"] == 1
    precision = result.children["Precision measures"]
    assert precision.dataframe.loc[:, "run-b"].iloc[0] == 2.0
    assert result.serialize()["type"] == "composite"
