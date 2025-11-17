from ..interfaces import Analysis, Result
from ..results import ValueResult
from resources.models import ResourceFile
from django import forms


class MockAnalysis3Form(forms.Form):
    prefix = "mock3"
    sample_choice = forms.ChoiceField(
        choices={
            "first": "FIRST CHOICE",
            "second": "SECOND CHOICE",
            "third": "THIRD_CHOICE",
        }
    )


class MockAnalysis3(Analysis):
    name = "Mock analysis 3"
    form_class = MockAnalysis3Form

    def execute(
        self,
        qrels_file: ResourceFile,
        queries_file: ResourceFile,
        retrieval_runs: list[ResourceFile],
        **parameters: dict,
    ) -> Result:
        return ValueResult(parameters["sample_choice"])
