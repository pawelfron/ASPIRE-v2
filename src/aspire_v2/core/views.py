from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView

from .models import Report, AnalysisResult, RetrievalRun, RetrievalTask
from resources.models import ResourceFile
from .forms import (
    ReportForm,
    RetrievalTaskUploadForm,
    RetrievalRunUploadForm,
    NewReportGeneralForm,
    NewReportRunsForm,
)

from .lib.utils import (
    get_report_class,
    create_analysis,
    load_qrel_file,
    load_queries_file,
    load_run_file,
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
            retrieval_task = get_object_or_404(
                RetrievalTask, pk=new_report["retrieval_task_id"]
            )
            retrieval_runs = get_list_or_404(
                RetrievalRun, pk__in=new_report["retrieval_run_ids"]
            )
            report = Report.objects.create(
                title=new_report["title"],
                description=new_report["description"],
                report_type=new_report["report_type"],
                author=request.user,
            )
            report.retrieval_runs.set(retrieval_runs)

            qrels = data_loaders_v2.load_qrel_file(retrieval_task)
            queries = data_loaders_v2.load_queries_file(retrieval_task)
            runs = {
                run.file.name: data_loaders_v2.load_run_file(run)
                for run in retrieval_runs
            }

            for analysis_name, analysis_parameters in parameters.items():
                analysis = create_analysis(analysis_name)

                result = analysis.execute(
                    qrels=qrels,
                    queries=queries,
                    retrieval_runs=runs,
                    **analysis_parameters,
                )

                AnalysisResult.objects.create(
                    report=report,
                    analysis_type=analysis_name,
                    parameters=analysis_parameters,
                    result=result.serialize(),
                )

            del request.session["new_report"]
            return redirect("view_report", report_id=report.id)

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
