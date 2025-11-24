from django.urls import path

from .views import FileUploadView, FileDetailView, FileListView, FileDeleteView


urlpatterns = [
    path("upload", FileUploadView.as_view(), name="file_upload"),
    path("<uuid:pk>", FileDetailView.as_view(), name="file_detail"),
    path("", FileListView.as_view(), name="file_list"),
    path("confirm_delete/<uuid:pk>", FileDeleteView.as_view(), name="file_delete"),
]
