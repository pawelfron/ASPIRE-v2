from django import forms
from django.forms import Form
from ...models import RetrievalTask, RetrievalRun


class AnalysisForm(Form):
    def __init__(
        self,
        *args,
        retrieval_task: RetrievalTask | None = None,
        retrieval_runs: list[RetrievalRun] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)


class RelevanceThresholdForm(AnalysisForm):
    """Analysis form with a relevance threshold bounded by the task's qrels."""

    relevance_threshold = forms.IntegerField(min_value=1)

    def __init__(self, *args, retrieval_task=None, retrieval_runs=None, **kwargs):
        super().__init__(
            *args,
            retrieval_task=retrieval_task,
            retrieval_runs=retrieval_runs,
            **kwargs,
        )

        if retrieval_task is None:
            return

        # Django compares the initial of a disabled field against its empty values,
        # which a numpy scalar cannot survive.
        max_relevance = int(retrieval_task.qrels_dataframe["relevance"].max())
        field = self.fields["relevance_threshold"]
        field.max_value = max_relevance
        field.initial = 1
        field.widget = forms.NumberInput(
            attrs={"step": "1", "min": "1", "max": max_relevance}
        )
        field.disabled = max_relevance == 1
