import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aspire_v2.settings")

app = Celery("aspire_v2")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
