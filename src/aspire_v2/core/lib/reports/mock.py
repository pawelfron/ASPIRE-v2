from ..interfaces import Report
from ..analyses import MockAnalysis, MockAnalysis2, OverallRetrievalCharacteristics


class MockReport(Report):
    name = "Mock report"
    analyses = [MockAnalysis, MockAnalysis2, OverallRetrievalCharacteristics]
