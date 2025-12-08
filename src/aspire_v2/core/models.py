from django.db import models
from django.utils.functional import cached_property
from accounts.models import User
import numpy as np
import pandas as pd

import uuid

# from .lib.analyses import all_analyses


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=250)
    description = models.TextField(max_length=500)
    report_type = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")


class AnalysisResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="results")
    analysis_type = models.CharField(max_length=100)
    parameters = models.JSONField()
    date = models.DateTimeField(auto_now_add=True)
    result = models.JSONField()

    # @property
    # def analysis_display_name(self):
    #     return all_analyses[self.analysis_type].name


class RetrievalTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    qrels = models.FileField(upload_to="qrels")
    topics = models.FileField(upload_to="topics")
    date = models.DateField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ir_tasks")

    def __str__(self):
        return self.title

    @cached_property
    def qrels_dataframe(self) -> pd.DataFrame:
        with self.qrels.open("rb") as f:
            return pd.read_csv(
                f,
                sep=" ",
                names=["query_id", "iteration", "doc_id", "relevance"],
                dtype={
                    "query_id": "object",
                    "iteration": "object",
                    "doc_id": "object",
                    "relevance": np.int32,
                },
            )


class RetrievalRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    file = models.FileField(upload_to="runs")
    date = models.DateField(auto_now_add=True)
    ir_task = models.ForeignKey(
        RetrievalTask, on_delete=models.CASCADE, related_name="retrieval_runs"
    )
    reports = models.ManyToManyField(Report, related_name="retrieval_runs")

    def __str__(self):
        return self.title

    @cached_property
    def dataframe(self) -> pd.DataFrame:
        with self.file.open("rb") as f:
            return pd.read_csv(
                f,
                sep="\t",
                names=["query_id", "iteration", "doc_id", "rank", "score", "tag"],
                dtype={
                    "query_id": "object",
                    "iteration": "object",
                    "doc_id": "object",
                    "rank": np.int32,
                    "score": np.float64,
                    "tag": "object",
                },
            )


class MeasureValue(models.Model):
    pk = models.CompositePrimaryKey("retrieval_run", "measure_name")
    retrieval_run = models.ForeignKey(
        RetrievalRun, on_delete=models.CASCADE, related_name="measures"
    )
    measure_name = models.CharField(max_length=100)
    value = models.FloatField()
