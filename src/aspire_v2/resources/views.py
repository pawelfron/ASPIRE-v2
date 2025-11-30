from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, CreateView

from .forms import UploadForm
from .models import ResourceFile


class FileUploadView(CreateView):
    model = ResourceFile
    form_class = UploadForm
    template_name = "resources/file_upload.html"
    success_url = reverse_lazy("file_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class FileDetailView(DetailView):
    model = ResourceFile
    template_name = "resources/file_detail.html"
    context_object_name = "object"


class FileListView(ListView):
    model = ResourceFile
    template_name = "resources/file_list.html"
    context_object_name = "files"
    paginate_by = 20

    def get_queryset(self):
        return ResourceFile.objects.filter(author=self.request.user).order_by("-date")


class FileDeleteView(DeleteView):
    model = ResourceFile
    success_url = reverse_lazy("file_list")
    template_name = "resources/file_confirm_delete.html"
