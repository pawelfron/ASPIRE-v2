from django import forms
from .models import Report, RetrievalTask, RetrievalRun
from .lib.reports import all_reports
from .lib.utils.file_validation import (
    QRELS_HELP,
    RUN_HELP,
    TOPICS_HELP,
    validate_qrels_file,
    validate_run_file,
    validate_topics_file,
)


class RetrievalTaskUploadForm(forms.ModelForm):
    class Meta:
        model = RetrievalTask
        fields = ("title", "description", "qrels", "topics")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["qrels"].help_text = QRELS_HELP
        self.fields["topics"].help_text = TOPICS_HELP

    def clean_qrels(self):
        uploaded = self.cleaned_data["qrels"]
        validate_qrels_file(uploaded)
        return uploaded

    def clean_topics(self):
        uploaded = self.cleaned_data["topics"]
        validate_topics_file(uploaded)
        return uploaded


class RetrievalRunUploadForm(forms.ModelForm):
    class Meta:
        model = RetrievalRun
        fields = ("title", "description", "ir_task", "file")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["ir_task"].label = "Retrieval task"
        self.fields["ir_task"].queryset = RetrievalTask.objects.filter(author=user)
        self.fields["ir_task"].empty_label = "---------"
        self.fields["file"].help_text = RUN_HELP

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        validate_run_file(uploaded)
        return uploaded


class RetrievalTaskMetadataForm(forms.ModelForm):
    class Meta:
        model = RetrievalTask
        fields = ("title", "description")


class RetrievalRunMetadataForm(forms.ModelForm):
    class Meta:
        model = RetrievalRun
        fields = ("title", "description")


class ReportMetadataForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ("title", "description")


class NewReportGeneralForm(forms.Form):
    title = forms.CharField(label="Title", max_length=100)
    description = forms.CharField(
        label="Description",
        max_length=500,
        required=False,
        widget=forms.Textarea(),
    )
    report_type = forms.ChoiceField(
        label="Report type",
        choices=[
            (slug, report_class.name) for slug, report_class in all_reports.items()
        ],
        widget=forms.RadioSelect({"class": "radio"}),
    )
    task = forms.ModelChoiceField(
        label="Retrieval task", queryset=RetrievalTask.objects.none()
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["task"].queryset = RetrievalTask.objects.filter(
            author=user
        ).order_by("-date")


class NewReportRunsForm(forms.Form):
    runs = forms.ModelMultipleChoiceField(
        label="Retrieval runs",
        queryset=RetrievalRun.objects.none(),
        widget=forms.CheckboxSelectMultiple({"class": "checkbox"}),
    )

    def __init__(self, task, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["runs"].queryset = RetrievalRun.objects.filter(
            ir_task=task
        ).order_by("-date")
