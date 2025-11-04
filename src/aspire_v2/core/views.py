from django.shortcuts import render

from .lib.interfaces import Report, Analysis
from .lib.reports import MockReport, MockReport2
from .lib.analyses import MockAnalysis, MockAnalysis2, MockAnalysis3

TEMP_MAPPING: dict[str, type[Report]] = {
    "mock1": MockReport,
    "mock2": MockReport2,
}

TEMP_ANALYSIS_MAPPING: dict[str, type[Analysis]] = {
    "mock1": MockAnalysis,
    "mock2": MockAnalysis2,
    "mock3": MockAnalysis3,
}


def dashboard(request):
    return render(request, "core/dashboard.html")


def list_reports(request):
    return render(
        request, "core/report_list.html", {"report_list": list(TEMP_MAPPING.keys())}
    )


def configure_report(request, report_slug: str):
    chosen_report = TEMP_MAPPING[report_slug]

    if request.method == "POST":
        forms = {
            analysis.name: analysis.form_class(request.POST)
            for analysis in chosen_report.analyses
        }

        if all(form.is_valid() for form in forms.values()):
            data = {key: form.cleaned_data for key, form in forms.items()}
            analyses = {
                key: TEMP_ANALYSIS_MAPPING[form.prefix]() for key, form in forms.items()
            }

            results = {}
            for key, analysis in analyses.items():
                result = analysis.execute("", "", [], **data[key])
                results[key] = result
            print(results)

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
