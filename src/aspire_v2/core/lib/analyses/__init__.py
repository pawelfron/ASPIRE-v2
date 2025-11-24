from ..interfaces import Analysis
from .overall_retrieval_characteristics import OverallRetrievalCharacteristics
from .precision_recall_curve import PrecisionRecallCurve

all_analyses: dict[str, type[Analysis]] = {
    "overall_retrieval_characteristics": OverallRetrievalCharacteristics,
    "precision_recall_curve": PrecisionRecallCurve,
}

__all__ = [all_analyses]
