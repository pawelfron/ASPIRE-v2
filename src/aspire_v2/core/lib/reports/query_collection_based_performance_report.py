from ..interfaces import Report
from ..analyses import (
    RelevanceJudgmentsPerQuery,
    RelevanceJudgmentsForMultipleQueries,
    DocumentsRetrievedByAllSystems,
    RelevanceRankingPositions,
)


class QueryCollectionBasedPerformanceReport(Report):
    name = "Query Collection Based Performance Report"
    analyses = [
        RelevanceJudgmentsPerQuery,
        RelevanceJudgmentsForMultipleQueries,
        DocumentsRetrievedByAllSystems,
        RelevanceRankingPositions,
    ]
