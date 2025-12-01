from ..interfaces import Report
from ..analyses import OverallRetrievalCharacteristics, PrecisionRecallCurve


class QueryBasedAnalysisReport(Report):
    name = "Query-based Analysis"
    analyses = [
        OverallRetrievalCharacteristics,
        PrecisionRecallCurve,
    ]
