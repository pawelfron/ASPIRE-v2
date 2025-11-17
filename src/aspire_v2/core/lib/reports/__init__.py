from .mock import MockReport
from .mock2 import MockReport2
from ..interfaces import Report

all_reports: dict[str, type[Report]] = {
    "mock1": MockReport,
    "mock2": MockReport2,
}

__all__ = [all_reports]
