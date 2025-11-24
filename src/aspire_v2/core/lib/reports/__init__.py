from ..interfaces import Report
from .retrieval_performance_report import RetrievalPerformanceReport

all_reports: dict[str, type[Report]] = {
    "retrieval_performance": RetrievalPerformanceReport,
}

__all__ = [all_reports]
