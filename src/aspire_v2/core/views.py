from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView

from .models import Report, AnalysisResult, RetrievalRun, RetrievalTask
from resources.models import ResourceFile
from .forms import ReportForm, RetrievalTaskUploadForm, RetrievalRunUploadForm

from .lib.utils import (
    get_report_class,
    create_analysis,
    load_qrel_file,
    load_queries_file,
    load_run_file,
)
from .lib.reports import all_reports


class ReportListView(ListView):
    model = Report
    template_name = "core/dashboard.html"
    context_object_name = "reports"
    paginate_by = 60

    def get_queryset(self):
        return Report.objects.filter(author=self.request.user).order_by("-date")


class ReportDeleteView(DeleteView):
    model = Report
    success_url = reverse_lazy("dashboard")
    template_name = "core/report_confirm_delete.html"


def new_report_general(request):
    if request.method == "POST":
        pass


def list_reports(request):
    return render(
        request, "core/report_list.html", {"report_list": list(all_reports.keys())}
    )


def configure_report(request, report_slug: str):
    chosen_report = get_report_class(report_slug)

    if request.method == "POST":
        main_form = ReportForm(request.user, request.POST)
        forms = {
            analysis.name: analysis.form_class(request.POST)
            for analysis in chosen_report.analyses
        }

        if all(form.is_valid() for form in forms.values()) and main_form.is_valid():
            report_data = main_form.cleaned_data
            report = Report(title=report_data["title"], author=request.user)
            report.save()

            data = {key: form.cleaned_data for key, form in forms.items()}
            analyses = {
                key: create_analysis(form.prefix) for key, form in forms.items()
            }

            qrel_file = get_object_or_404(ResourceFile, pk=report_data["qrel_file"])
            queries_file = get_object_or_404(
                ResourceFile, pk=report_data["queries_file"]
            )
            runs_files = get_list_or_404(ResourceFile, pk__in=report_data["runs_files"])

            qrels = load_qrel_file(qrel_file)
            queries = load_queries_file(queries_file)
            retrieval_runs = {
                run_file.file.name: load_run_file(run_file) for run_file in runs_files
            }

            for key, analysis in analyses.items():
                result = analysis.execute(
                    qrels=qrels,
                    queries=queries,
                    retrieval_runs=retrieval_runs,
                    **data[key],
                )
                analysis_result = AnalysisResult(
                    report=report,
                    analysis_type=key,
                    parameters=data[key],
                    result=result.serialize(),
                )
                analysis_result.save()

            return redirect("view_report", report_id=report.id)

    return render(
        request,
        "core/configure.html",
        {
            "analysis_forms": {
                analysis.name: analysis.form_class
                for analysis in chosen_report.analyses
            },
            "main_form": ReportForm(user=request.user),
        },
    )


def view_report(request, report_id: str):
    report = get_object_or_404(Report, pk=report_id)
    plot_data = {}
    for result in report.results.all():
        data = result.result
        if data["type"] == "plot":
            plot_data[result.analysis_type] = data
        elif data["type"] == "composite":
            for label, sub_result in data["value"].items():
                if sub_result["type"] == "plot":
                    plot_data[f"{result.analysis_type}-{label}"] = sub_result
    return render(
        request,
        "core/report.html",
        {"report": report, "plot_data": plot_data},
    )


class RetrievalTaskListView(ListView):
    model = RetrievalTask
    template_name = "core/retrieval_task_list.html"
    context_object_name = "tasks"
    paginate_by = 60

    def get_queryset(self):
        return RetrievalTask.objects.filter(author=self.request.user).order_by("-date")


class RetrievalTaskDetailView(DetailView):
    model = RetrievalTask
    template_name = "core/retrieval_task_detail.html"
    context_object_name = "task"


class RetrievalTaskUploadView(CreateView):
    model = RetrievalTask
    form_class = RetrievalTaskUploadForm
    template_name = "core/retrieval_task_upload.html"
    success_url = reverse_lazy("retrieval_task_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class RetrievalTaskDeleteView(DeleteView):
    model = RetrievalTask
    success_url = reverse_lazy("retrieval_task_list")
    template_name = "core/retrieval_task_confirm_delete.html"
    context_object_name = "task"


class RetrievalRunListView(ListView):
    model = RetrievalRun
    template_name = "core/retrieval_run_list.html"
    context_object_name = "runs"
    paginate_by = 60

    def get_queryset(self):
        return RetrievalRun.objects.filter(ir_task__author=self.request.user).order_by(
            "-date"
        )


class RetrievalRunDetailView(DetailView):
    model = RetrievalRun
    template_name = "core/retrieval_run_detail.html"
    context_object_name = "run"


class RetrievalRunUploadView(CreateView):
    model = RetrievalRun
    form_class = RetrievalRunUploadForm
    template_name = "core/retrieval_run_upload.html"
    success_url = reverse_lazy("retrieval_run_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class RetrievalRunDeleteView(DeleteView):
    model = RetrievalRun
    success_url = reverse_lazy("retrieval_run_list")
    template_name = "core/retrieval_run_confirm_delete.html"
    context_object_name = "run"
