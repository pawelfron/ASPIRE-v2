from ..interfaces import Analysis, Result
from ..results import ValueResult
from django import forms


class MockAnalysis2Form(forms.Form):
    prefix = "mock2"
    sample_number = forms.IntegerField()


class MockAnalysis2(Analysis):
    name = "Mock analysis 2"
    form_class = MockAnalysis2Form

    def execute(
        self,
        qrels_file: str,
        queries_file: str,
        retrieval_runs: list[str],
        **parameters: dict,
    ) -> Result:
        return ValueResult(parameters["sample_number"])
