from django.forms import Form
import pandas as pd


class AnalysisForm(Form):
    def __init__(
        self,
        qrels: pd.DataFrame,
        queries: pd.DataFrame,
        retrieval_runs: dict[str, pd.DataFrame],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
