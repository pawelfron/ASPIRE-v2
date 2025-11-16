from ..interfaces import Analysis, Result
from ..results import ValueResult

from django import forms


class OverallRetrievalCharacteristicsForm(forms.Form):
    prefix = "overall_retrieval_characteristics"


class OverallRetrievalCharacteristics(Analysis):
    name = "Overall Retrieval Characteristics"
    form_class = OverallRetrievalCharacteristicsForm

    def execute(
        self,
        qrels_file: str,
        queries_file: str,
        retrieval_runs: list[str],
        **parameters: dict,
    ) -> Result:
        return ValueResult(1)
