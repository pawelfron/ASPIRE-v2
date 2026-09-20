from ..interfaces import Report
from ..analyses import (
    RelevanceJudgmentsPerQuery,
    QueryTextWordClouds,
    QueryPerformanceVsQueryLength,
)


class QueryTextBasedPerformanceReport(Report):
    name = "Query Text-based Performance Report"
    analyses = [
        RelevanceJudgmentsPerQuery,
        QueryTextWordClouds,
        QueryPerformanceVsQueryLength,
    ]
