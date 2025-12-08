from celery import shared_task
from django.shortcuts import get_list_or_404, get_object_or_404
from django.contrib.auth import get_user_model
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
