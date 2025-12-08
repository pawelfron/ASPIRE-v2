from ..interfaces import Analysis, Result, AnalysisForm
from ..results import TableResult
from ...models import RetrievalRun, RetrievalTask
from ..utils.measure_calculation import get_measure_value
import pandas as pd
from ..measures import NumberOfQueries, NumberOfRelevantDocuments, NumberOfResults

from django import forms


class OverallRetrievalCharacteristicsForm(forms.Form):
    prefix = "overall_retrieval_characteristics"


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
                get_measure_value(retrieval_run, measure) for measure in measures
            ]

        return TableResult(result)
