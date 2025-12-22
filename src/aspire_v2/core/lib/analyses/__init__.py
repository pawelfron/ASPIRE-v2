from ..interfaces import Analysis
from .overall_retrieval_characteristics import OverallRetrievalCharacteristics
from .precision_recall_curve import PrecisionRecallCurve
from .experimental_evaluation import ExperimentalEvaluation
from .positional_distribution import PositionalDistribution
from .retrieved_document_intersection import RetrievedDocumentInterseciton
from .documents_retrieved_by_all_systems import DocumentsRetrievedByAllSystems
from .relevance_judgments_per_query import RelevanceJudgmentsPerQuery
from .relevance_judgments_for_multiple_queries import (
    RelevanceJudgmentsForMultipleQueries,
)
from .relevance_ranking_positions import RelevanceRankingPositions

all_analyses: dict[str, type[Analysis]] = {
    "overall_retrieval_characteristics": OverallRetrievalCharacteristics,
    "precision_recall_curve": PrecisionRecallCurve,
    "experimental_evaluation": ExperimentalEvaluation,
    "positional_distribution": PositionalDistribution,
    "retrieved_document_intersection": RetrievedDocumentInterseciton,
    "documents_retrieved_by_all_systems": DocumentsRetrievedByAllSystems,
    "relevance_judgments_per_query": RelevanceJudgmentsPerQuery,
    "relevance_judgments_for_multiple_queries": RelevanceJudgmentsForMultipleQueries,
    "relevance_ranking_positions": RelevanceRankingPositions,
}

__all__ = [all_analyses]
