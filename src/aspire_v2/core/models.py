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


class RetrievalTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    qrels = models.FileField(upload_to="res")
    topics = models.FileField(upload_to="res")
    date = models.DateField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ir_tasks")


class RetrievalRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    file = models.FileField(upload_to="res")
    date = models.DateField(auto_now_add=True)
    ir_task = models.ForeignKey(
        RetrievalTask, on_delete=models.CASCADE, related_name="retrieval_runs"
    )
    reports = models.ManyToManyField(Report, related_name="retrieval_runs")
