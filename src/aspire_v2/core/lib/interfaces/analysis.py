from abc import ABC, abstractmethod
from typing import ClassVar

from .result import Result

from django import forms


class Analysis(ABC):
    """Base class for all analyses."""

    name: ClassVar[str]
    form_class: ClassVar[type[forms.Form]]

    @abstractmethod
    def execute(
        self,
        qrels_file: str,
        queries_file: str,
        retrieval_runs: list[str],
        **parameters: dict,
    ) -> Result:
        """Execute the analysis."""
