from ..interfaces import Report
from ..analyses import OverallRetrievalCharacteristics, PrecisionRecallCurve


class RetrievalPerformanceReport(Report):
    name = "Retrieval Performance Evaluation Report"
    analyses = [
        OverallRetrievalCharacteristics,
        PrecisionRecallCurve,
    ]
