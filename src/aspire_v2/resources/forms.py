from django.forms import ModelForm

from .models import ResourceFile


class UploadForm(ModelForm):
    class Meta:
        model = ResourceFile
        fields = ("title", "file", "file_type")
