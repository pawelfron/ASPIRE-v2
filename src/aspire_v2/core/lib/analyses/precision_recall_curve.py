from ..interfaces import Analysis, Result, AnalysisForm
from ..results import PlotResult
from ...models import RetrievalRun, RetrievalTask
import plotly.graph_objects as go
from ir_measures import parse_measure, calc_aggregate

from django import forms


class PrecisionRecallCurveForm(AnalysisForm):
    prefix = "precision_recall_curve"

    relevance_threshold = forms.IntegerField(min_value=1)

    def __init__(self, *args, retrieval_task=None, retrieval_runs=None, **kwargs):
        super().__init__(
            *args,
            retrieval_task=retrieval_task,
            retrieval_runs=retrieval_runs,
            **kwargs,
        )

        if retrieval_task and retrieval_runs:
            max_relevance = retrieval_task.qrels_dataframe["relevance"].max()
            self.fields["relevance_threshold"].max_value = max_relevance
            self.fields["relevance_threshold"].widget = forms.NumberInput(
                attrs={
                    "type": "range",
                    "step": "1",
                    "min": "1",
                    "max": max_relevance,
                }
            )
            self.fields["relevance_threshold"].disabled = max_relevance == 1


class PrecisionRecallCurve(Analysis):
    name = "Precision/Recall Curve"
    form_class = PrecisionRecallCurveForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        relevance_threshold = parameters["relevance_threshold"]
        x = [i / 10.0 for i in range(11)]

        measure_names = [f"IPrec(rel={relevance_threshold})@{cutoff}" for cutoff in x]
        measures = [parse_measure(measure_name) for measure_name in measure_names]

        qrels = retrieval_task.qrels_dataframe
        runs_dfs = {run.title: run.dataframe for run in retrieval_runs}
        agg_result = {
            name: calc_aggregate(measures, qrels, df) for name, df in runs_dfs.items()
        }

        precisions = {
            name: [res[measure] for measure in measures]
            for name, res in agg_result.items()
        }

        fig = go.Figure()

        for name, y in precisions.items():
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name))

        fig.update_layout(
            title="Precision/Recall Curve",
            xaxis_title="Recall",
            yaxis_title="Precision",
            legend=dict(x=1, y=1),
            hovermode="x unified",
        )

        return PlotResult(fig)
