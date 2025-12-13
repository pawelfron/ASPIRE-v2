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
