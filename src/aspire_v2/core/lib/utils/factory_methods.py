from django.http import Http404

from ..interfaces import Report, Analysis
from .mappings import REPORT_MAPPING, ANALYSIS_MAPPING


def get_report_class(report_type_slug: str) -> type[Report]:
    if (report_class := REPORT_MAPPING.get(report_type_slug)) is None:
        raise Http404
    return report_class


def create_analysis(analysis_type_slug: str) -> Analysis:
    if (analysis_class := ANALYSIS_MAPPING.get(analysis_type_slug)) is None:
        raise Http404
    return analysis_class()
