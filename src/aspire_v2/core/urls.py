from django.urls import path

from .views import dashboard, configure_report, list_reports, view_report


urlpatterns = [
    path("dashboard", dashboard, name="dashboard"),
    path("report", list_reports, name="list_reports"),
    path("report/<slug:report_slug>", configure_report, name="new_report"),
    path("view_report/<uuid:report_id>", view_report, name="view_report"),
]
