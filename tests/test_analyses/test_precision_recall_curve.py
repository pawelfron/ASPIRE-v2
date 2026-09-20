from unittest.mock import patch

from core.lib.analyses.precision_recall_curve import (
    PrecisionRecallCurve,
    PrecisionRecallCurveForm,
)
from core.lib.results.plot import PlotResult


def test_form_prefix(fake_task, fake_runs):
    form = PrecisionRecallCurveForm()
    assert form.prefix == "precision_recall_curve"
    form = PrecisionRecallCurveForm(retrieval_task=fake_task, retrieval_runs=fake_runs)
    assert form.prefix == "precision_recall_curve"
    assert form.fields["relevance_threshold"].initial == 2


@patch("core.lib.analyses.precision_recall_curve.get_aggregate_measure")
def test_execute_plots_one_trace_per_run(mock_measure, fake_task, fake_runs):
    mock_measure.side_effect = (
        lambda run, measure: 0.5 if run.title == "run-a" else 0.25
    )
    result = PrecisionRecallCurve().execute(
        fake_task, fake_runs, relevance_threshold=1
    )
    assert isinstance(result, PlotResult)
    assert len(result.fig.data) == 2
    assert result.fig.data[0].name == "run-a"
    assert list(result.fig.data[0].x) == [i / 10.0 for i in range(11)]
    assert result.fig.layout.title.text == "Precision/Recall Curve"
    assert result.serialize()["type"] == "plot"
