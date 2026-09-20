from types import SimpleNamespace
from unittest.mock import patch

from core.lib.measures import NumberOfQueries, NumberOfRelevantDocuments
from core.lib.utils.measure_calculation import (
    get_aggregate_measure,
    get_per_query_measure,
)
from core.models import MeasureValue


@patch("core.lib.utils.measure_calculation.MeasureValue.objects")
def test_get_aggregate_measure_returns_cached_value(mock_objects, fake_runs):
    mock_objects.get.return_value = SimpleNamespace(value=0.42)
    run = fake_runs[0]

    assert get_aggregate_measure(run, NumberOfQueries()) == 0.42
    mock_objects.get.assert_called_once_with(pk=(run.id, "NumQ"))
    mock_objects.create.assert_not_called()


@patch("core.lib.utils.measure_calculation.MeasureValue.objects")
def test_get_aggregate_measure_computes_and_caches_on_miss(mock_objects, fake_runs):
    mock_objects.get.side_effect = MeasureValue.DoesNotExist
    run = fake_runs[0]
    measure = NumberOfQueries()

    value = get_aggregate_measure(run, measure)

    assert value == 2.0
    mock_objects.create.assert_called_once_with(
        retrieval_run=run,
        measure_name="NumQ",
        value=2.0,
    )


@patch("core.lib.utils.measure_calculation.MeasureValue.objects")
def test_get_aggregate_measure_computes_numrel(mock_objects, fake_runs):
    mock_objects.get.side_effect = MeasureValue.DoesNotExist
    value = get_aggregate_measure(fake_runs[0], NumberOfRelevantDocuments(rel=1))
    assert value == 4.0


def test_get_per_query_measure_returns_query_scores(fake_runs):
    scores = get_per_query_measure(fake_runs[0], NumberOfQueries())
    assert scores == {"q1": 1.0, "q2": 1.0}
