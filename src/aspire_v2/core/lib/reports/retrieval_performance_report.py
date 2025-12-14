from ..interfaces import Report
from ..analyses import (
    OverallRetrievalCharacteristics,
    PrecisionRecallCurve,
    ExperimentalEvaluation,
    PositionalDistribution,
    RetrievedDocumentInterseciton,
    DocumentsRetrievedByAllSystems,
)


class RetrievalPerformanceReport(Report):
    name = "Retrieval Performance Evaluation"
    analyses = [
        OverallRetrievalCharacteristics,
        ExperimentalEvaluation,
        PositionalDistribution,
        PrecisionRecallCurve,
        RetrievedDocumentInterseciton,
        DocumentsRetrievedByAllSystems,
    ]
