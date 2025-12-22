from ..interfaces import Report
from .retrieval_performance_report import RetrievalPerformanceReport
from .query_collection_based_performance_report import (
    QueryCollectionBasedPerformanceReport,
)

all_reports: dict[str, type[Report]] = {
    "retrieval_performance": RetrievalPerformanceReport,
    "collection_based": QueryCollectionBasedPerformanceReport,
}

__all__ = [all_reports]
