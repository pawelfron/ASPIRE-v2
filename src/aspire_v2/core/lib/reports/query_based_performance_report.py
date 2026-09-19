from ..interfaces import Report
from ..analyses import (
    RelevanceJudgmentsPerQuery,
    PerQueryPerformance,
    PerQueryPerformanceVsBaseline,
    PerQueryPerformanceVsThreshold,
)


class QueryBasedPerformanceReport(Report):
    name = "Query-based Performance Report"
    analyses = [
        RelevanceJudgmentsPerQuery,
        PerQueryPerformance,
        PerQueryPerformanceVsBaseline,
        PerQueryPerformanceVsThreshold,
    ]
