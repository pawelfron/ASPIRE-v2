from ..interfaces import Analysis, Measure, Result, AnalysisForm
from ..results import CompositeResult, TableResult
from ...models import RetrievalRun, RetrievalTask
from ..utils.measure_calculation import get_aggregate_measure
import pandas as pd
from ..measures import (
    NumberOfQueries,
    NumberOfRelevantDocuments,
    NumberOfRelevantRetrievedDocuments,
    PercentageOfRelevantDocsInCutoff,
    RPrecision,
    Recall,
)

from django import forms


class OverallRetrievalCharacteristicsForm(AnalysisForm):
    prefix = "overall_retrieval_characteristics"

    relevance_threshold = forms.IntegerField(min_value=1)

    def __init__(self, *args, retrieval_task=None, retrieval_runs=None, **kwargs):
        super().__init__(
            *args,
            retrieval_task=retrieval_task,
            retrieval_runs=retrieval_runs,
            **kwargs,
        )

        if retrieval_task and retrieval_runs:
            # Django compares the initial of a disabled field against its empty
            # values, which a numpy scalar cannot survive.
            max_relevance = int(retrieval_task.qrels_dataframe["relevance"].max())
            self.fields["relevance_threshold"].max_value = max_relevance
            self.fields["relevance_threshold"].initial = max_relevance
            self.fields["relevance_threshold"].widget = forms.NumberInput(
                attrs={
                    # "type": "range",
                    "step": "1",
                    "min": "1",
                    "max": max_relevance,
                }
            )
            self.fields["relevance_threshold"].disabled = max_relevance == 1


class OverallRetrievalCharacteristics(Analysis):
    name = "Overall Retrieval Characteristics"
    form_class = OverallRetrievalCharacteristicsForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        relevance_threshold = int(parameters["relevance_threshold"])

        overall_measures: list[Measure] = [
            NumberOfQueries(),
            # No ir_measures provider implements NumRel at a relevance level other
            # than its default, so this one measure cannot follow the threshold.
            NumberOfRelevantDocuments(rel=1),
            NumberOfRelevantRetrievedDocuments(rel=relevance_threshold),
        ]
        precision_measures: list[Measure] = [
            PercentageOfRelevantDocsInCutoff(
                rel=relevance_threshold, cutoff=cutoff, judged_only=False
            )
            for cutoff in (5, 10, 25, 50, 100)
        ] + [RPrecision(rel=relevance_threshold)]
        recall_measures: list[Measure] = [
            Recall(rel=relevance_threshold, cutoff=cutoff, judged_only=False)
            for cutoff in (50, 1000)
        ]

        return CompositeResult(
            {
                "Overall measures": TableResult(
                    self._build_table(retrieval_runs, overall_measures, as_int=True)
                ),
                "Precision measures": TableResult(
                    self._build_table(retrieval_runs, precision_measures)
                ),
                "Recall measures": TableResult(
                    self._build_table(retrieval_runs, recall_measures)
                ),
            }
        )

    def _build_table(
        self,
        retrieval_runs: list[RetrievalRun],
        measures: list[Measure],
        as_int: bool = False,
    ) -> pd.DataFrame:
        table = pd.DataFrame(index=[measure.measure_name for measure in measures])
        for retrieval_run in retrieval_runs:
            values = [
                get_aggregate_measure(retrieval_run, measure) for measure in measures
            ]
            table[retrieval_run.title] = (
                [int(value) for value in values]
                if as_int
                else [round(value, 4) for value in values]
            )

        return table
