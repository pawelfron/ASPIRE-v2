from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.template.loader import render_to_string
import pdfkit

from .tasks import create_report
from .models import Report, AnalysisResult, RetrievalRun, RetrievalTask
from .forms import (
    RetrievalTaskUploadForm,
    RetrievalRunUploadForm,
    NewReportGeneralForm,
    NewReportRunsForm,
)

from .lib.utils import (
    create_analysis,
)
from .lib.utils import data_loaders_v2
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
        form = NewReportGeneralForm(request.user, request.POST)
        if form.is_valid():
            request.session["new_report"] = {
                "title": form.cleaned_data["title"],
                "description": form.cleaned_data["description"],
                "report_type": form.cleaned_data["report_type"],
                "retrieval_task_id": str(form.cleaned_data["task"].id),
            }
            return redirect("new_report_runs")
    else:
        form = NewReportGeneralForm(request.user)

    return render(request, "core/new_report_general.html", {"form": form})


def new_report_runs(request):
    if (new_report := request.session.get("new_report")) is None:
        return redirect("new_report_general")

    retrieval_task = get_object_or_404(
        RetrievalTask,
        pk=new_report["retrieval_task_id"],
    )

    if request.method == "POST":
        form = NewReportRunsForm(retrieval_task, request.POST)
        if form.is_valid():
            request.session["new_report"]["retrieval_run_ids"] = [
                str(run.id) for run in form.cleaned_data["runs"]
            ]
            request.session.modified = True
            return redirect("new_report_parameters")
    else:
        form = NewReportRunsForm(retrieval_task)

    return render(
        request,
        "core/new_report_runs.html",
        {"form": form, "new_report": new_report, "retrieval_task": retrieval_task},
    )


def new_report_parameters(request):
    if (new_report := request.session.get("new_report")) is None:
        return redirect("new_report_general")

    if "retrieval_run_ids" not in new_report:
        return redirect("new_report_runs")

    if (report_class := all_reports.get(new_report["report_type"])) is None:
        pass

    analysis_forms = {
        analysis.form_class.prefix: analysis.form_class
        for analysis in report_class.analyses
    }

    if request.method == "POST":
        parameters = {}
        all_valid = True
        for name, form_class in analysis_forms.items():
            form = form_class(request.POST)
            if form.is_valid():
                parameters[name] = form.cleaned_data
            else:
                all_valid = False
                break

        if all_valid:
            report = Report.objects.create(
                title=new_report["title"],
                description=new_report["description"],
                report_type=new_report["report_type"],
                author=request.user,
            )

            create_report.delay_on_commit(
                report_id=report.id,
                retrieval_task_id=new_report["retrieval_task_id"],
                retrieval_run_ids=new_report["retrieval_run_ids"],
                parameters=parameters,
            )

            del request.session["new_report"]
            return redirect("report_status", report_id=report.id)

    forms = {name: form_class() for name, form_class in analysis_forms.items()}

    return render(
        request,
        "core/new_report_parameters.html",
        {"forms": forms, "new_report": new_report, "report_class": report_class},
    )


def new_report_cancel(request):
    if "new_report" in request.session:
        del request.session["new_report"]
    return redirect("dashboard")


def report_status(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    return render(
        request,
        "core/report_status.html",
        {"report": report},
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


def generate_pdf(request, report_id: str):
    if request.method == "POST":
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

        report_html = render_to_string(
            "core/report_pdf.html",
            {"report": report, "plot_data": plot_data},
        )
        pdf = pdfkit.from_string(report_html, False)


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
