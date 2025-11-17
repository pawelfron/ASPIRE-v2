from ..interfaces import Analysis, Result
from ..results import ValueResult
from resources.models import ResourceFile

from django import forms


class OverallRetrievalCharacteristicsForm(forms.Form):
    prefix = "overall_retrieval_characteristics"


class OverallRetrievalCharacteristics(Analysis):
    name = "Overall Retrieval Characteristics"
    form_class = OverallRetrievalCharacteristicsForm

    def execute(
        self,
        qrels_file: ResourceFile,
        queries_file: ResourceFile,
        retrieval_runs: list[ResourceFile],
        **parameters: dict,
    ) -> Result:
        return ValueResult(1)
