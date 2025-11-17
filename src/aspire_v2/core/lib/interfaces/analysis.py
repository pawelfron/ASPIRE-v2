from abc import ABC, abstractmethod
from typing import ClassVar

from .result import Result
from resources.models import ResourceFile

from django import forms


class Analysis(ABC):
    """Base class for all analyses."""

    name: ClassVar[str]
    form_class: ClassVar[type[forms.Form]]

    @abstractmethod
    def execute(
        self,
        qrels_file: ResourceFile,
        queries_file: ResourceFile,
        retrieval_runs: list[ResourceFile],
        **parameters: dict,
    ) -> Result:
        """Execute the analysis."""
