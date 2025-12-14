from celery import shared_task
from django.shortcuts import get_list_or_404, get_object_or_404
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from playwright.sync_api import sync_playwright
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Report, AnalysisResult, RetrievalTask, RetrievalRun
from .lib.utils import create_analysis

User = get_user_model()


@shared_task
def create_report(
    report_id: str,
    retrieval_task_id: str,
    retrieval_run_ids: list[str],
    parameters: dict[str, dict],
):
    channel_layer = get_channel_layer()

    retrieval_task = get_object_or_404(RetrievalTask, pk=retrieval_task_id)
    retrieval_runs = get_list_or_404(RetrievalRun, pk__in=retrieval_run_ids)
    report = get_object_or_404(Report, pk=report_id)
    report.retrieval_runs.set(retrieval_runs)

    for i, (analysis_name, analysis_parameters) in enumerate(parameters.items()):
        analysis = create_analysis(analysis_name)

        result = analysis.execute(
            retrieval_task=retrieval_task,
            retrieval_runs=retrieval_runs,
            **analysis_parameters,
        )

        AnalysisResult.objects.create(
            report=report,
            analysis_type=analysis_name,
            parameters=analysis_parameters,
            result=result.serialize(),
        )

        async_to_sync(channel_layer.group_send)(
            f"report.{report_id}",
            {
                "type": "analysis_complete",
                "progress": i + 1,
                "total": len(parameters),
            },
        )

    async_to_sync(channel_layer.group_send)(
        f"report.{report_id}",
        {
            "type": "report_complete",
            "total": len(parameters),
        },
    )

    return "Completed"


@shared_task
def generate_pdf(report_id: str):
    channel_layer = get_channel_layer()

    report = get_object_or_404(Report, pk=report_id)
    plot_data = {}
    for result in report.results.all():
        data = result.result
        if data["type"] == "plot":
            plot_data[result.analysis_type] = data
        elif data["type"] == "composite":
            for label, sub_result in data["value"].items():
                if sub_result["type"] == "plot":
                    plot_data[f"{result.analysis_type}-{label}"] = sub_result

    with open("/app/src/aspire_v2/static/css/output.css", "r") as f:
        css_content = f.read()

    report_html = render_to_string(
        "core/report_pdf.html",
        {"report": report, "plot_data": plot_data, "css_content": css_content},
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(report_html)
        page.wait_for_timeout(2000)
        pdf_bytes = page.pdf(format="A4", print_background=True)
        browser.close()

    report.pdf.save(f"report_{report_id}.pdf", ContentFile(pdf_bytes), save=True)

    async_to_sync(channel_layer.group_send)(
        f"pdf.{report_id}",
        {"type": "pdf_complete"},
    )

    return "Generated"
