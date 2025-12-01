from django.urls import path

from .views import (
    configure_report,
    list_reports,
    view_report,
    ReportListView,
    new_report_general,
    new_report_runs,
    new_report_parameters,
    new_report_cancel,
    ReportDeleteView,
    RetrievalTaskListView,
    RetrievalTaskDetailView,
    RetrievalTaskUploadView,
    RetrievalTaskDeleteView,
    RetrievalRunListView,
    RetrievalRunDetailView,
    RetrievalRunUploadView,
    RetrievalRunDeleteView,
)


urlpatterns = [
    path("dashboard", ReportListView.as_view(), name="dashboard"),
    path("new_report_general", new_report_general, name="new_report_general"),
    path("new_report_runs", new_report_runs, name="new_report_runs"),
    path("new_report_parameters", new_report_parameters, name="new_report_parameters"),
    path("new_report_cancel", new_report_cancel, name="new_report_cancel"),
    path("report", list_reports, name="list_reports"),
    path("report/<slug:report_slug>", configure_report, name="new_report"),
    path("view_report/<uuid:report_id>", view_report, name="view_report"),
    path("confirm_delete/<uuid:pk>", ReportDeleteView.as_view(), name="report_delete"),
    path("tasks", RetrievalTaskListView.as_view(), name="retrieval_task_list"),
    path(
        "tasks/<uuid:pk>",
        RetrievalTaskDetailView.as_view(),
        name="retrieval_task_detail",
    ),
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
    path("runs/upload", RetrievalRunUploadView.as_view(), name="retrieval_run_upload"),
    path(
        "runs/confirm_delete/<uuid:pk>",
        RetrievalRunDeleteView.as_view(),
        name="retrieval_run_delete",
    ),
]
