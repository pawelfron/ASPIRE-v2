from abc import ABC, abstractmethod
from typing import ClassVar

from django.forms import Form

from ...models import RetrievalTask, RetrievalRun
from .result import Result
from .analysis_form import AnalysisForm


class Analysis(ABC):
    """Base class for all analyses."""

    name: ClassVar[str]
    form_class: ClassVar[type[AnalysisForm]]

    @abstractmethod
    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        """Execute the analysis."""
