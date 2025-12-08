# chat/routing.py
from django.urls import re_path

from .consumers import ReportGenerationConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/report_status/(?P<report_id>[A-Za-z0-9_-]+)/$",
        ReportGenerationConsumer.as_asgi(),
    ),
]
