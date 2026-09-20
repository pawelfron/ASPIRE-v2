from django.http import Http404

from ..interfaces import Report, Analysis


def get_report_class(report_type_slug: str) -> type[Report]:
    from ..reports import all_reports

    if (report_class := all_reports.get(report_type_slug)) is None:
        raise Http404
    return report_class


def create_analysis(analysis_type_slug: str) -> Analysis:
    from ..analyses import all_analyses

    if (analysis_class := all_analyses.get(analysis_type_slug)) is None:
        raise Http404
    return analysis_class()
