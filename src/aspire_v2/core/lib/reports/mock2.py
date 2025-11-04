from ..interfaces import Report
from ..analyses import MockAnalysis2, MockAnalysis3


class MockReport2(Report):
    name = "Alternative mock report"
    analyses = [MockAnalysis2, MockAnalysis3]
