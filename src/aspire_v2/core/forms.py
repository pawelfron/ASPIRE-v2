from django import forms
from .models import RetrievalTask, RetrievalRun
from .lib.reports import all_reports


class RetrievalTaskUploadForm(forms.ModelForm):
    class Meta:
        model = RetrievalTask
        fields = ("title", "description", "qrels", "topics")


class RetrievalRunUploadForm(forms.ModelForm):
    class Meta:
        model = RetrievalRun
        fields = ("title", "description", "ir_task", "file")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        tasks = RetrievalTask.objects.filter(author=user)
        self.fields["ir_task"].label = "Retrieval task"
        self.fields["ir_task"].choices = [(task.id, task.title) for task in tasks]


class NewReportGeneralForm(forms.Form):
    title = forms.CharField(label="Title", max_length=100)
    description = forms.CharField(
        label="Description", max_length=500, widget=forms.Textarea()
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
