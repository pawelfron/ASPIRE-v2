from ..interfaces import Report, Analysis
from ..reports import MockReport, MockReport2
from ..analyses import (
    MockAnalysis,
    MockAnalysis2,
    MockAnalysis3,
    OverallRetrievalCharacteristics,
)

REPORT_MAPPING: dict[str, Report] = {"mock1": MockReport, "mock2": MockReport2}

ANALYSIS_MAPPING: dict[str, Analysis] = {
    "mock1": MockAnalysis,
    "mock2": MockAnalysis2,
    "mock3": MockAnalysis3,
    "overall_retrieval_characteristics": OverallRetrievalCharacteristics,
}
