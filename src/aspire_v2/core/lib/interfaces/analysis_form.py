from django.forms import Form
from ...models import RetrievalTask, RetrievalRun


class AnalysisForm(Form):
    def __init__(
        self,
        *args,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
