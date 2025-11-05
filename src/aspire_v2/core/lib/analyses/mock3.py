from ..interfaces import Analysis, Result
from ..results import ValueResult
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
        qrels_file: str,
        queries_file: str,
        retrieval_runs: list[str],
        **parameters: dict,
    ) -> Result:
        return ValueResult(parameters["sample_choice"])
