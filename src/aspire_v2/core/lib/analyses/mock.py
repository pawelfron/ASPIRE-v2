from ..interfaces import Analysis, Result
from ..results import ValueResult
from django import forms


class MockAnalysisForm(forms.Form):
    prefix = "mock1"
    sample_text = forms.CharField(max_length=200)


class MockAnalysis(Analysis):
    name = "Mock analysis"
    form_class = MockAnalysisForm

    def execute(
        self,
        qrels_file: str,
        queries_file: str,
        retrieval_runs: list[str],
        **parameters: dict,
    ) -> Result:
        return ValueResult(parameters["sample_text"])
