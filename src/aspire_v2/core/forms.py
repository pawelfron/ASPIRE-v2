from django import forms
from resources.models import ResourceFile


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
