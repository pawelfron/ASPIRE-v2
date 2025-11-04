from ..interfaces import Report
from ..analyses import MockAnalysis, MockAnalysis2


class MockReport(Report):
    name = "Mock report"
    analyses = [MockAnalysis, MockAnalysis2]
