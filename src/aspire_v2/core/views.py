import json
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder

from .tasks import (
    create_report,
    generate_pdf,
    recalculate_analysis,
    recalculating_cache_key,
    invalidate_report_pdf,
    RECALCULATING_CACHE_TIMEOUT,
)
from .models import Report, AnalysisResult, RetrievalRun, RetrievalTask
from .forms import (
    RetrievalTaskUploadForm,
    RetrievalTaskMetadataForm,
    RetrievalRunUploadForm,
    RetrievalRunMetadataForm,
    ReportMetadataForm,
    NewReportGeneralForm,
    NewReportRunsForm,
)

from .lib.reports import all_reports
from .lib.analyses import all_analyses


class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = "core/dashboard.html"
    context_object_name = "reports"
    paginate_by = 60

    def get_queryset(self):
        return Report.objects.filter(author=self.request.user).order_by("-date")


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = Report
    success_url = reverse_lazy("dashboard")
    template_name = "core/report_confirm_delete.html"


class ReportEditView(LoginRequiredMixin, UpdateView):
    model = Report
    form_class = ReportMetadataForm
    template_name = "core/metadata_edit.html"
    pk_url_kwarg = "report_id"

    def get_queryset(self):
        return Report.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Edit report"
        context["cancel_url"] = reverse(
            "view_report", kwargs={"report_id": self.object.pk}
        )
        return context

    def form_valid(self, form):
        previous = Report.objects.get(pk=form.instance.pk)
        changed = (
            previous.title != form.cleaned_data["title"]
            or previous.description != form.cleaned_data["description"]
        )
        response = super().form_valid(form)
        if changed:
            invalidate_report_pdf(self.object)
        return response

    def get_success_url(self):
        return reverse("view_report", kwargs={"report_id": self.object.pk})


@login_required
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


@login_required
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


@login_required
def new_report_parameters(request):
    if (new_report := request.session.get("new_report")) is None:
        return redirect("new_report_general")

    if "retrieval_run_ids" not in new_report:
        return redirect("new_report_runs")

    if (report_class := all_reports.get(new_report["report_type"])) is None:
        pass

    retrieval_task = get_object_or_404(
        RetrievalTask, pk=new_report["retrieval_task_id"]
    )
    retrieval_runs = get_list_or_404(
        RetrievalRun, pk__in=new_report["retrieval_run_ids"]
    )

    analysis_forms = {
        analysis.form_class.prefix: analysis.form_class
        for analysis in report_class.analyses
    }

    if request.method == "POST":
        parameters = {}
        all_valid = True
        for name, form_class in analysis_forms.items():
            form = form_class(
                request.POST,
                retrieval_task=retrieval_task,
                retrieval_runs=retrieval_runs,
            )
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

    forms = [
        {
            "name": analysis.name,
            "form": analysis.form_class(
                retrieval_task=retrieval_task,
                retrieval_runs=retrieval_runs,
            ),
        }
        for analysis in report_class.analyses
    ]

    return render(
        request,
        "core/new_report_parameters.html",
        {"forms": forms, "new_report": new_report, "report_class": report_class},
    )


@login_required
def new_report_cancel(request):
    if "new_report" in request.session:
        del request.session["new_report"]
    return redirect("dashboard")


@login_required
def report_status(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    return render(
        request,
        "core/report_status.html",
        {"report": report},
    )


def _recalculating_ids(results) -> list:
    return [
        result.id
        for result in results
        if cache.get(recalculating_cache_key(result.id))
    ]


@login_required
def view_report(request, report_id: str):
    report = get_object_or_404(Report, pk=report_id)
    results = list(report.results.all())
    recalculating_ids = _recalculating_ids(results)
    plot_data = {}
    for result in results:
        if result.id in recalculating_ids:
            continue
        data = result.result
        if data["type"] == "plot":
            plot_data[result.analysis_type] = data
        elif data["type"] == "composite":
            for label, sub_result in data["value"]:
                if sub_result["type"] == "plot":
                    plot_data[f"{result.analysis_type}-{label}"] = sub_result

    pdf_is_generating = False
    if request.method == "POST" and not report.pdf and not recalculating_ids:
        generate_pdf.delay(report_id)
        pdf_is_generating = True

    return render(
        request,
        "core/report.html",
        {
            "report": report,
            "plot_data": plot_data,
            "pdf_is_generating": pdf_is_generating,
            "recalculating_ids": recalculating_ids,
        },
    )


@login_required
def edit_analysis_parameters(request, report_id: str, analysis_id: str):
    report = get_object_or_404(Report, pk=report_id)
    analysis_result = get_object_or_404(
        AnalysisResult, pk=analysis_id, report=report
    )
    if cache.get(recalculating_cache_key(analysis_result.id)):
        return redirect("view_report", report_id=report.id)

    retrieval_runs = list(report.retrieval_runs.all())
    if not retrieval_runs:
        raise Http404
    retrieval_task = retrieval_runs[0].ir_task

    analysis_class = all_analyses.get(analysis_result.analysis_type)
    if analysis_class is None:
        raise Http404
    form_class = analysis_class.form_class

    form = form_class(
        request.POST or None,
        initial=analysis_result.parameters,
        retrieval_task=retrieval_task,
        retrieval_runs=retrieval_runs,
    )

    if request.method == "POST" and form.is_valid():
        parameters = json.loads(json.dumps(form.cleaned_data, cls=DjangoJSONEncoder))
        invalidate_report_pdf(report)
        cache.set(
            recalculating_cache_key(analysis_result.id),
            True,
            timeout=RECALCULATING_CACHE_TIMEOUT,
        )
        recalculate_analysis.delay_on_commit(str(analysis_result.id), parameters)
        return redirect("view_report", report_id=report.id)

    return render(
        request,
        "core/edit_analysis_parameters.html",
        {
            "report": report,
            "analysis_result": analysis_result,
            "form": form,
        },
    )


# def generate_pdf_view(request, report_id: str):
#     if request.method == "POST":
#         generate_pdf.delay(report_id)
#         return redirect(
#             "view_report", report_id=report_id, kwargs={"pdf_is_generating": True}
#         )


@login_required
def download_pdf(request, report_id: str):
    report = get_object_or_404(Report, pk=report_id)

    response = FileResponse(
        report.pdf.open("rb"),
        content_type="application/pdf",
        as_attachment=True,
        filename=f"{report.title}.pdf",
    )

    return response


def _file_download(field):
    return FileResponse(
        field.open("rb"),
        as_attachment=True,
        filename=Path(field.name).name,
    )


@login_required
def download_qrels(request, pk):
    task = get_object_or_404(RetrievalTask, pk=pk, author=request.user)
    return _file_download(task.qrels)


@login_required
def download_topics(request, pk):
    task = get_object_or_404(RetrievalTask, pk=pk, author=request.user)
    return _file_download(task.topics)


@login_required
def download_run_file(request, pk):
    run = get_object_or_404(RetrievalRun, pk=pk, ir_task__author=request.user)
    return _file_download(run.file)


class RetrievalTaskListView(LoginRequiredMixin, ListView):
    model = RetrievalTask
    template_name = "core/retrieval_task_list.html"
    context_object_name = "tasks"
    paginate_by = 60

    def get_queryset(self):
        return RetrievalTask.objects.filter(author=self.request.user).order_by("-date")


class RetrievalTaskDetailView(LoginRequiredMixin, DetailView):
    model = RetrievalTask
    template_name = "core/retrieval_task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return RetrievalTask.objects.filter(author=self.request.user)


class RetrievalTaskEditView(LoginRequiredMixin, UpdateView):
    model = RetrievalTask
    form_class = RetrievalTaskMetadataForm
    template_name = "core/metadata_edit.html"
    context_object_name = "task"

    def get_queryset(self):
        return RetrievalTask.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Edit retrieval task"
        context["cancel_url"] = reverse(
            "retrieval_task_detail", kwargs={"pk": self.object.pk}
        )
        return context

    def get_success_url(self):
        return reverse("retrieval_task_detail", kwargs={"pk": self.object.pk})


class RetrievalTaskUploadView(LoginRequiredMixin, CreateView):
    model = RetrievalTask
    form_class = RetrievalTaskUploadForm
    template_name = "core/retrieval_task_upload.html"
    success_url = reverse_lazy("retrieval_task_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class RetrievalTaskDeleteView(LoginRequiredMixin, DeleteView):
    model = RetrievalTask
    success_url = reverse_lazy("retrieval_task_list")
    template_name = "core/retrieval_task_confirm_delete.html"
    context_object_name = "task"


class RetrievalRunListView(LoginRequiredMixin, ListView):
    model = RetrievalRun
    template_name = "core/retrieval_run_list.html"
    context_object_name = "runs"
    paginate_by = 60

    def get_queryset(self):
        return RetrievalRun.objects.filter(ir_task__author=self.request.user).order_by(
            "-date"
        )


class RetrievalRunDetailView(LoginRequiredMixin, DetailView):
    model = RetrievalRun
    template_name = "core/retrieval_run_detail.html"
    context_object_name = "run"

    def get_queryset(self):
        return RetrievalRun.objects.filter(ir_task__author=self.request.user)


class RetrievalRunEditView(LoginRequiredMixin, UpdateView):
    model = RetrievalRun
    form_class = RetrievalRunMetadataForm
    template_name = "core/metadata_edit.html"
    context_object_name = "run"

    def get_queryset(self):
        return RetrievalRun.objects.filter(ir_task__author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["heading"] = "Edit retrieval run"
        context["cancel_url"] = reverse(
            "retrieval_run_detail", kwargs={"pk": self.object.pk}
        )
        return context

    def get_success_url(self):
        return reverse("retrieval_run_detail", kwargs={"pk": self.object.pk})


class RetrievalRunUploadView(LoginRequiredMixin, CreateView):
    model = RetrievalRun
    form_class = RetrievalRunUploadForm
    template_name = "core/retrieval_run_upload.html"
    success_url = reverse_lazy("retrieval_run_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class RetrievalRunDeleteView(LoginRequiredMixin, DeleteView):
    model = RetrievalRun
    success_url = reverse_lazy("retrieval_run_list")
    template_name = "core/retrieval_run_confirm_delete.html"
    context_object_name = "run"
