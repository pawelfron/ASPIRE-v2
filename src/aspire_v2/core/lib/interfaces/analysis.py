from abc import ABC, abstractmethod
from typing import ClassVar

import pandas as pd
from django.forms import Form

from .result import Result
from .analysis_form import AnalysisForm


class Analysis(ABC):
    """Base class for all analyses."""

    name: ClassVar[str]
    form_class: ClassVar[type[Form]]

    @abstractmethod
    def execute(
        self,
        qrels: pd.DataFrame,
        queries: pd.DataFrame,
        retrieval_runs: dict[str, pd.DataFrame],
        **parameters: dict,
    ) -> Result:
        """Execute the analysis."""
