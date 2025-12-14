from ..interfaces import Analysis, Result, AnalysisForm
from ..results import TableResult
from ...models import RetrievalRun, RetrievalTask
from ..utils.measure_calculation import get_aggregate_measure
import pandas as pd
from ..measures import NumberOfQueries, NumberOfRelevantDocuments, NumberOfResults

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


class OverallRetrievalCharacteristics(Analysis):
    name = "Overall Retrieval Characteristics"
    form_class = OverallRetrievalCharacteristicsForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        measures = [
            NumberOfQueries(),
            NumberOfRelevantDocuments(rel=1),
            NumberOfResults(rel=1),
        ]

        result = pd.DataFrame(index=[measure.measure_name for measure in measures])
        for retrieval_run in retrieval_runs:
            result[retrieval_run.title] = [
                get_aggregate_measure(retrieval_run, measure) for measure in measures
            ]

        return TableResult(result)
