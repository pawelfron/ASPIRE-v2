from ..interfaces import Analysis, Result, AnalysisForm, Measure
from ..results import TableResult, CompositeResult
from ...models import RetrievalRun, RetrievalTask
from ..utils.measure_calculation import get_per_query_measure
from ..measures import (
    AveragePrecision,
    PercentageOfRelevantDocsInCutoff,
    nDCG,
    Recall,
    MeanReciprocalRank,
)
import numpy as np
import pandas as pd
import scipy

from django import forms


class ExperimentalEvaluationForm(AnalysisForm):
    prefix = "experimental_evaluation"

    relevance_threshold = forms.IntegerField(min_value=1)
    baseline_run = forms.ChoiceField(
        label="Baseline run", choices=[("", "Select a baseline run")]
    )
    correction_method = forms.ChoiceField(
        label="Correction method",
        choices=[
            ("Bonferroni", "Bonferroni"),
            ("Holm", "Holm"),
            ("Holm-Sidak", "Holm-Sidak"),
        ],
    )
    correction_value = forms.FloatField(
        label="Correction value (alpha)",
        min_value=0.01,
        max_value=0.05,
        initial=0.05,
        widget=forms.NumberInput(
            attrs={
                "type": "range",
                "step": "0.01",
                "min": "0.01",
                "max": "0.05",
            }
        ),
    )

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
            self.fields["relevance_threshold"].initial = 1

            self.fields["baseline_run"].choices = [("", "Select a baseline run")] + [
                (retrieval_run.id, retrieval_run.title)
                for retrieval_run in retrieval_runs
            ]


class ExperimentalEvaluation(Analysis):
    name = "Experimental Evaluation"
    form_class = ExperimentalEvaluationForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        relevance_threshold = parameters["relevance_threshold"]

        measures: list[Measure] = [
            AveragePrecision(rel=relevance_threshold, cutoff=100, judged_only=False),
            PercentageOfRelevantDocsInCutoff(
                rel=relevance_threshold, cutoff=10, judged_only=False
            ),
            nDCG(cutoff=10, judged_only=True, dcg="log2"),
            Recall(rel=relevance_threshold, cutoff=50, judged_only=False),
            MeanReciprocalRank(rel=relevance_threshold, cutoff=100, judged_only=False),
        ]

        measure_values = {
            retrieval_run.title: {
                measure.measure_name: get_per_query_measure(retrieval_run, measure)
                for measure in measures
            }
            for retrieval_run in retrieval_runs
        }

        measure_values_table = pd.DataFrame(
            index=[measure.measure_name for measure in measures]
        )
        for title, values in measure_values.items():
            measure_values_table[title] = [
                np.mean(list(per_query_values.values()))
                for measure_name, per_query_values in values.items()
            ]

        baseline_run = list(
            filter(
                lambda run: str(run.id) != parameters["baseline_run"],
                retrieval_runs,
            )
        )[0]
        runs_to_compare = list(
            filter(
                lambda run: str(run.id) != parameters["baseline_run"], retrieval_runs
            )
        )

        p_values_table = pd.DataFrame(
            index=[measure.measure_name for measure in measures]
        )
        for run in runs_to_compare:
            p_values = []
            for measure in measures:
                baseline_query_ids = measure_values[baseline_run.title][
                    measure.measure_name
                ].keys()
                baseline_values = measure_values[baseline_run.title][
                    measure.measure_name
                ].values()

                run_query_ids = measure_values[run.title][measure.measure_name].keys()
                run_values = measure_values[run.title][measure.measure_name].values()

                common_query_ids = run_query_ids & baseline_query_ids
                baseline_values = [
                    v
                    for v, qid in zip(baseline_values, baseline_query_ids)
                    if qid in common_query_ids
                ]
                run_values = [
                    v
                    for v, qid in zip(run_values, run_query_ids)
                    if qid in common_query_ids
                ]
                result = scipy.stats.ttest_rel(baseline_values, run_values)
                p_values.append(None if np.isnan(result.pvalue) else result.pvalue)
            p_values_table[run.title] = p_values

        return CompositeResult(
            {
                "Measure values": TableResult(measure_values_table),
                "P-values": TableResult(p_values_table),
            }
        )
