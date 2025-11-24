from ..interfaces import Analysis, Result, AnalysisForm
from ..results import PlotResult
import pandas as pd
import plotly.graph_objects as go
from ir_measures import parse_measure, calc_aggregate

from django import forms


class PrecisionRecallCurveForm(forms.Form):
    prefix = "precision_recall_curve"


class PrecisionRecallCurve(Analysis):
    name = "Precision/Recall Curve"
    form_class = PrecisionRecallCurveForm

    def execute(
        self,
        qrels: pd.DataFrame,
        queries: pd.DataFrame,
        retrieval_runs: dict[str, pd.DataFrame],
        **parameters: dict,
    ) -> Result:
        relevance_threshold = 1
        x = [i / 10.0 for i in range(11)]

        measure_names = [f"IPrec(rel={relevance_threshold})@{cutoff}" for cutoff in x]
        measures = [parse_measure(measure_name) for measure_name in measure_names]
        agg_result = {
            name: calc_aggregate(measures, qrels, retrieval_run)
            for name, retrieval_run in retrieval_runs.items()
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
