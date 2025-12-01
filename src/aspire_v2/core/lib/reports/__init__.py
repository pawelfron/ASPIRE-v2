from ..interfaces import Report
from .retrieval_performance_report import RetrievalPerformanceReport
from .query_based_analysis_report import QueryBasedAnalysisReport

all_reports: dict[str, type[Report]] = {
    "retrieval_performance": RetrievalPerformanceReport,
    "query_based": QueryBasedAnalysisReport,
}

__all__ = [all_reports]
