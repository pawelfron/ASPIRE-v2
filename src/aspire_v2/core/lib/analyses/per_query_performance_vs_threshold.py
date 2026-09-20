from ..interfaces import Analysis, AnalysisForm, Measure, Result
from ...models import RetrievalRun, RetrievalTask
from ..measures import nDCG
from ..results import CompositeResult, PlotResult, TableResult, ValueResult
from ..utils.per_query import (
    DIFFERENCE_SUMMARY_ROWS,
    PerQueryValues,
    difference_summary_column,
    get_per_query_measures,
    per_measure_bar_figure,
    summarize_differences,
)
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from django import forms


class PerQueryPerformanceVsThresholdForm(AnalysisForm):
    prefix = "per_query_performance_vs_threshold"

    threshold = forms.FloatField(
        label=(
            "Performance threshold (0.0 compares each experiment against the median "
            "of the others)"
        ),
        min_value=0.0,
        max_value=1.0,
        initial=0.0,
        widget=forms.NumberInput(attrs={"step": "0.05", "min": "0", "max": "1"}),
    )


class PerQueryPerformanceVsThreshold(Analysis):
    name = "Experimental Evaluation per Query vs Median/Threshold"
    form_class = PerQueryPerformanceVsThresholdForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        threshold = float(parameters["threshold"])

        # nDCG has no relevance cut-off of its own, so this analysis needs no
        # relevance threshold parameter.
        measures: list[Measure] = [nDCG(cutoff=10, judged_only=False, dcg="log2")]
        measure_names = [measure.measure_name for measure in measures]

        values, query_ids = get_per_query_measures(retrieval_runs, measures)

        if threshold == 0.0:
            return self._compare_to_median(values, measure_names, query_ids)

        return self._compare_to_threshold(values, measure_names, query_ids, threshold)

    def _compare_to_median(
        self,
        values: PerQueryValues,
        measure_names: list[str],
        query_ids: list[str],
    ) -> Result:
        """Compare each experiment against the median of the remaining N-1."""
        run_titles = list(values)

        if len(run_titles) < 2:
            return CompositeResult(
                {
                    "Median comparison": ValueResult(
                        "Comparing an experiment against the median of the others "
                        "requires at least two retrieval runs. Pick a non-zero "
                        "threshold to compare against a fixed value instead."
                    )
                }
            )

        results = {}
        summaries: dict[str, dict[str, list]] = {
            measure_name: {} for measure_name in measure_names
        }

        for run_title in run_titles:
            actual = {
                measure_name: {
                    other: list(values[other][measure_name].values())
                    for other in run_titles
                }
                for measure_name in measure_names
            }
            fig = per_measure_bar_figure(
                actual,
                query_ids,
                f"Per-query performance of {run_title} against the median of the "
                f"other {len(run_titles) - 1} experiments",
            )

            for row, measure_name in enumerate(measure_names, start=1):
                medians = self._median_of_others(
                    values, run_titles, run_title, measure_name, query_ids
                )
                fig.add_trace(
                    go.Scatter(
                        x=query_ids,
                        y=medians,
                        mode="markers",
                        name="Median (N-1)",
                        marker=dict(
                            color="red",
                            symbol="star",
                            size=10,
                            line=dict(width=0.5, color="DarkSlateGrey"),
                        ),
                        showlegend=row == 1,
                        hovertemplate=(
                            "Query: %{x}<br>Median (N-1): %{y:.3f}<extra></extra>"
                        ),
                    ),
                    row=row,
                    col=1,
                )

                summaries[measure_name][run_title] = difference_summary_column(
                    summarize_differences(
                        [values[run_title][measure_name][q] for q in query_ids],
                        medians,
                        query_ids,
                    )
                )

            results[f"Median comparison - {run_title}"] = PlotResult(fig)

        for measure_name in measure_names:
            results[f"Summary vs median - {measure_name}"] = TableResult(
                pd.DataFrame(summaries[measure_name], index=DIFFERENCE_SUMMARY_ROWS)
            )

        return CompositeResult(results)

    def _compare_to_threshold(
        self,
        values: PerQueryValues,
        measure_names: list[str],
        query_ids: list[str],
        threshold: float,
    ) -> Result:
        differences = {
            measure_name: {
                run_title: [
                    values[run_title][measure_name][query_id] - threshold
                    for query_id in query_ids
                ]
                for run_title in values
            }
            for measure_name in measure_names
        }

        results = {
            "Per-query difference from threshold": PlotResult(
                per_measure_bar_figure(
                    differences,
                    query_ids,
                    f"Per-query performance difference from the threshold "
                    f"{threshold:.2f}",
                    yaxis_suffix=" difference from threshold",
                    zero_line=True,
                )
            )
        }

        reference = [threshold] * len(query_ids)
        for measure_name in measure_names:
            columns = {
                run_title: difference_summary_column(
                    summarize_differences(
                        [values[run_title][measure_name][q] for q in query_ids],
                        reference,
                        query_ids,
                    )
                )
                for run_title in values
            }
            results[f"Summary vs threshold - {measure_name}"] = TableResult(
                pd.DataFrame(columns, index=DIFFERENCE_SUMMARY_ROWS)
            )

        return CompositeResult(results)

    def _median_of_others(
        self,
        values: PerQueryValues,
        run_titles: list[str],
        current: str,
        measure_name: str,
        query_ids: list[str],
    ) -> list[float]:
        others = [title for title in run_titles if title != current]
        return [
            float(
                np.median([values[other][measure_name][query_id] for other in others])
            )
            for query_id in query_ids
        ]
