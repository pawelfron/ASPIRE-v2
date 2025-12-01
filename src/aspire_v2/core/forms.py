from django import forms
from resources.models import ResourceFile
from .models import RetrievalTask, RetrievalRun
from .lib.reports import all_reports


class ReportForm(forms.Form):
    prefix = "__report__"
    title = forms.CharField(label="Report title")
    qrel_file = forms.ChoiceField(
        label="Qrel file",
        choices=[],
    )
    queries_file = forms.ChoiceField(
        label="Queries file",
        choices=[],
    )
    runs_files = forms.MultipleChoiceField(
        label="Runs files",
        choices=[],
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qrel_files = ResourceFile.objects.filter(author=user, file_type="QREL")
        queries_files = ResourceFile.objects.filter(author=user, file_type="QUERIES")
        runs_files = ResourceFile.objects.filter(author=user, file_type="RUNS")

        self.fields["qrel_file"].choices = [(f.id, f.title) for f in qrel_files]
        self.fields["queries_file"].choices = [(f.id, f.title) for f in queries_files]
        self.fields["runs_files"].choices = [(f.id, f.title) for f in runs_files]


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


# class NewReportGeneralForm(forms.Form):
#     title = forms.CharField(max_length=100)
#     description = forms.Textarea(max_length=500)
#     report_type = forms.ChoiceField(
#         choices=[(slug, name) for slug, name in all_reports.items()]
#     )
#     task = forms.ChoiceField(choices=[])

#     def __init__(self, user, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         tasks = RetrievalTask.objects.filter(author=user)
#         self.fields["task"].choices = [(task.id, task.title) for task in tasks]


# class NewReportRunsForm(forms.Form):
#     runs = forms.MultipleChoiceField(label="Retrieval runs", choices=[])

#     def __init__(self, task, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         runs = RetrievalRun.objects.filter(ir_task=task)
#         self.fields["runs"].choices = [(run.id, run.title) for run in runs]
