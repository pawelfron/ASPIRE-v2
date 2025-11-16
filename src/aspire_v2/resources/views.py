from django.shortcuts import render, redirect

from .forms import UploadForm


def upload_file(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
        else:
            print(form.errors)
    else:
        form = UploadForm()
    return render(request, "resources/upload_file.html", {"form": form})
