from .mock import MockAnalysis
from .mock2 import MockAnalysis2
from .mock3 import MockAnalysis3
from .overall_retrieval_characteristics import OverallRetrievalCharacteristics
from ..interfaces import Analysis

all_analyses: dict[str, type[Analysis]] = {
    "mock1": MockAnalysis,
    "mock2": MockAnalysis2,
    "mock3": MockAnalysis3,
    "overall_retrieval_characteristics": OverallRetrievalCharacteristics,
}

__all__ = [all_analyses]
