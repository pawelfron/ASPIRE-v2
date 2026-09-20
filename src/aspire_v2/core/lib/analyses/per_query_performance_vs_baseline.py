from ..interfaces import Analysis, Measure, RelevanceThresholdForm, Result
from ...models import RetrievalRun, RetrievalTask
from ..measures import PercentageOfRelevantDocsInCutoff, Recall
from ..results import CompositeResult, PlotResult, TableResult
from ..utils.per_query import (
    DIFFERENCE_SUMMARY_ROWS,
    difference_summary_column,
    get_per_query_measures,
    per_measure_bar_figure,
    summarize_differences,
)
import pandas as pd

from django import forms


class PerQueryPerformanceVsBaselineForm(RelevanceThresholdForm):
    prefix = "per_query_performance_vs_baseline"

    baseline_run = forms.ChoiceField(
        label="Baseline run", choices=[("", "Select a baseline run")]
    )

    def __init__(self, *args, retrieval_task=None, retrieval_runs=None, **kwargs):
        super().__init__(
            *args,
            retrieval_task=retrieval_task,
            retrieval_runs=retrieval_runs,
            **kwargs,
        )

        if retrieval_runs:
            self.fields["baseline_run"].choices = [("", "Select a baseline run")] + [
                (retrieval_run.id, retrieval_run.title)
                for retrieval_run in retrieval_runs
            ]


class PerQueryPerformanceVsBaseline(Analysis):
    name = "Experimental Evaluation per Query vs Baseline"
    form_class = PerQueryPerformanceVsBaselineForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        relevance_threshold = int(parameters["relevance_threshold"])

        measures: list[Measure] = [
            PercentageOfRelevantDocsInCutoff(
                rel=relevance_threshold, cutoff=10, judged_only=False
            ),
            Recall(rel=relevance_threshold, cutoff=10, judged_only=False),
        ]
        measure_names = [measure.measure_name for measure in measures]

        baseline_run = next(
            run for run in retrieval_runs if str(run.id) == parameters["baseline_run"]
        )
        compared_runs = [run for run in retrieval_runs if run != baseline_run]

        values, query_ids = get_per_query_measures(retrieval_runs, measures)

        differences = {
            measure_name: {
                run.title: [
                    values[run.title][measure_name][query_id]
                    - values[baseline_run.title][measure_name][query_id]
                    for query_id in query_ids
                ]
                for run in compared_runs
            }
            for measure_name in measure_names
        }

        results = {
            "Per-query difference from baseline": PlotResult(
                per_measure_bar_figure(
                    differences,
                    query_ids,
                    f"Per-query performance difference from the baseline "
                    f"{baseline_run.title}",
                    yaxis_suffix=" difference",
                    zero_line=True,
                )
            )
        }

        for measure_name in measure_names:
            columns = {
                run.title: difference_summary_column(
                    summarize_differences(
                        [values[run.title][measure_name][q] for q in query_ids],
                        [
                            values[baseline_run.title][measure_name][q]
                            for q in query_ids
                        ],
                        query_ids,
                    )
                )
                for run in compared_runs
            }
            results[f"Summary vs baseline - {measure_name}"] = TableResult(
                pd.DataFrame(columns, index=DIFFERENCE_SUMMARY_ROWS)
            )

        return CompositeResult(results)
