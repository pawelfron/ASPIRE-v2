from abc import ABC
from typing import ClassVar

from .analysis import Analysis


class Report(ABC):
    """Base class for all reports."""

    name: ClassVar[str]
    analyses: ClassVar[list[type[Analysis]]]
