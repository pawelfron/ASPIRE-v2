from django.urls import path

from .views import (
    view_report,
    edit_analysis_parameters,
    ReportListView,
    new_report_general,
    new_report_runs,
    new_report_parameters,
    new_report_cancel,
    report_status,
    # generate_pdf_view,
    download_pdf,
    download_qrels,
    download_topics,
    download_run_file,
    ReportDeleteView,
    ReportEditView,
    RetrievalTaskListView,
    RetrievalTaskDetailView,
    RetrievalTaskEditView,
    RetrievalTaskUploadView,
    RetrievalTaskDeleteView,
    RetrievalRunListView,
    RetrievalRunDetailView,
    RetrievalRunEditView,
    RetrievalRunUploadView,
    RetrievalRunDeleteView,
)


urlpatterns = [
    path("dashboard", ReportListView.as_view(), name="dashboard"),
    path("new_report_general", new_report_general, name="new_report_general"),
    path("new_report_runs", new_report_runs, name="new_report_runs"),
    path("new_report_parameters", new_report_parameters, name="new_report_parameters"),
    path("new_report_cancel", new_report_cancel, name="new_report_cancel"),
    path("view_report/<uuid:report_id>", view_report, name="view_report"),
    path(
        "view_report/<uuid:report_id>/analysis/<uuid:analysis_id>/parameters",
        edit_analysis_parameters,
        name="edit_analysis_parameters",
    ),
    path("report_status/<uuid:report_id>", report_status, name="report_status"),
    path("confirm_delete/<uuid:pk>", ReportDeleteView.as_view(), name="report_delete"),
    # path("view_report/<uuid:report_id>/pdf", generate_pdf_view, name="generate_pdf"),
    path("view_report/<uuid:report_id>/download", download_pdf, name="download_pdf"),
    path(
        "view_report/<uuid:report_id>/edit",
        ReportEditView.as_view(),
        name="report_edit",
    ),
    path("tasks", RetrievalTaskListView.as_view(), name="retrieval_task_list"),
    path(
        "tasks/<uuid:pk>",
        RetrievalTaskDetailView.as_view(),
        name="retrieval_task_detail",
    ),
    path(
        "tasks/<uuid:pk>/edit",
        RetrievalTaskEditView.as_view(),
        name="retrieval_task_edit",
    ),
    path("tasks/<uuid:pk>/qrels", download_qrels, name="download_qrels"),
    path("tasks/<uuid:pk>/topics", download_topics, name="download_topics"),
    path(
        "tasks/upload", RetrievalTaskUploadView.as_view(), name="retrieval_task_upload"
    ),
    path(
        "tasks/confirm_delete/<uuid:pk>",
        RetrievalTaskDeleteView.as_view(),
        name="retrieval_task_delete",
    ),
    path("runs", RetrievalRunListView.as_view(), name="retrieval_run_list"),
    path(
        "runs/<uuid:pk>",
        RetrievalRunDetailView.as_view(),
        name="retrieval_run_detail",
    ),
    path(
        "runs/<uuid:pk>/edit",
        RetrievalRunEditView.as_view(),
        name="retrieval_run_edit",
    ),
    path("runs/<uuid:pk>/file", download_run_file, name="download_run_file"),
    path("runs/upload", RetrievalRunUploadView.as_view(), name="retrieval_run_upload"),
    path(
        "runs/confirm_delete/<uuid:pk>",
        RetrievalRunDeleteView.as_view(),
        name="retrieval_run_delete",
    ),
]
