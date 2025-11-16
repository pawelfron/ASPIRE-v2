from django.db import models

from accounts.models import User

import uuid


class ResourceFile(models.Model):
    class FileType(models.TextChoices):
        QREL = "QREL"
        QUERIES = "QUERIES"
        RUNS = "RUNS"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=250)
    file = models.FileField(upload_to="res")
    file_type = models.CharField(max_length=7, choices=FileType)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resources")
