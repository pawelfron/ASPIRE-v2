from django.db import models
from accounts.models import User

import uuid


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=250)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")


class AnalysisResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="results")
    analysis_type = models.CharField(max_length=100)
    parameters = models.JSONField()
    date = models.DateTimeField(auto_now_add=True)
    result = models.JSONField()
