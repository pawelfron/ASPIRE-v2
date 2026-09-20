from ..interfaces import Report
from .retrieval_performance_report import RetrievalPerformanceReport
from .query_based_performance_report import QueryBasedPerformanceReport
from .query_text_based_performance_report import QueryTextBasedPerformanceReport
from .query_collection_based_performance_report import (
    QueryCollectionBasedPerformanceReport,
)

all_reports: dict[str, type[Report]] = {
    "retrieval_performance": RetrievalPerformanceReport,
    "query_based": QueryBasedPerformanceReport,
    "query_text_based": QueryTextBasedPerformanceReport,
    "collection_based": QueryCollectionBasedPerformanceReport,
}

__all__ = [all_reports]
