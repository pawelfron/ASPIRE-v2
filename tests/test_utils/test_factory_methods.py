import pytest
from django.http import Http404

from core.lib.analyses import all_analyses
from core.lib.reports import all_reports
from core.lib.utils.factory_methods import create_analysis, get_report_class


@pytest.mark.parametrize("slug", list(all_analyses))
def test_create_analysis_resolves_known_slugs(slug):
    analysis = create_analysis(slug)
    assert isinstance(analysis, all_analyses[slug])


def test_create_analysis_unknown_slug_raises_404():
    with pytest.raises(Http404):
        create_analysis("not-an-analysis")


@pytest.mark.parametrize("slug", list(all_reports))
def test_get_report_class_resolves_known_slugs(slug):
    report_class = get_report_class(slug)
    assert report_class is all_reports[slug]


def test_get_report_class_unknown_slug_raises_404():
    with pytest.raises(Http404):
        get_report_class("not-a-report")
