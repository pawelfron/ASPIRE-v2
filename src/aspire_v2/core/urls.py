from django.urls import path

from .views import (
    configure_report,
    list_reports,
    view_report,
    ReportListView,
    ReportDeleteView,
)


urlpatterns = [
    path("dashboard", ReportListView.as_view(), name="dashboard"),
    path("report", list_reports, name="list_reports"),
    path("report/<slug:report_slug>", configure_report, name="new_report"),
    path("view_report/<uuid:report_id>", view_report, name="view_report"),
    path("confirm_delete/<uuid:pk>", ReportDeleteView.as_view(), name="report_delete"),
]
