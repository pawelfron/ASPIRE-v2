from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404

from .models import Report, AnalysisResult

from .lib.utils import get_report_class, create_analysis
from .lib.utils.mappings import REPORT_MAPPING


def dashboard(request):
    return render(request, "core/dashboard.html")


def list_reports(request):
    return render(
        request, "core/report_list.html", {"report_list": list(REPORT_MAPPING.keys())}
    )


def configure_report(request, report_slug: str):
    chosen_report = get_report_class(report_slug)

    if request.method == "POST":
        forms = {
            analysis.name: analysis.form_class(request.POST)
            for analysis in chosen_report.analyses
        }

        if all(form.is_valid() for form in forms.values()):
            report = Report(title="placeholder")
            report.save()

            data = {key: form.cleaned_data for key, form in forms.items()}
            analyses = {
                key: create_analysis(form.prefix) for key, form in forms.items()
            }

            for key, analysis in analyses.items():
                result = analysis.execute("", "", [], **data[key])
                analysis_result = AnalysisResult(
                    report=report,
                    analysis_type=key,
                    parameters=data[key],
                    result=result.serialize(),
                )
                analysis_result.save()

            return redirect("view_report", report_id=report.id)

    return render(
        request,
        "core/configure.html",
        {
            "analysis_forms": {
                analysis.name: analysis.form_class
                for analysis in chosen_report.analyses
            }
        },
    )


def view_report(request, report_id: str):
    report = get_object_or_404(Report, pk=report_id)
    analysis_results = get_list_or_404(AnalysisResult, report=report)
    return render(
        request,
        "core/report.html",
        {"analysis_results": analysis_results, "title": report.title},
    )
