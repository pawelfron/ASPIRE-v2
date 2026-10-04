from django.contrib import admin

from .models import AnalysisResult, Report, RetrievalRun, RetrievalTask

# MeasureValue uses a composite primary key. Django's admin refuses to
# register those models (ImproperlyConfigured).


class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "report_type", "author", "date", "content_revision")
    list_filter = ("report_type", "date")
    search_fields = ("title", "description", "author__email")
    date_hierarchy = "date"
    ordering = ("-date",)
    readonly_fields = ("id", "date")
    autocomplete_fields = ("author",)


class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("analysis_type", "report", "date")
    list_filter = ("analysis_type", "date")
    search_fields = ("analysis_type", "report__title")
    date_hierarchy = "date"
    ordering = ("-date",)
    readonly_fields = ("id", "date")
    autocomplete_fields = ("report",)


class RetrievalTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "date")
    search_fields = ("title", "description", "author__email")
    date_hierarchy = "date"
    ordering = ("-date",)
    readonly_fields = ("id", "date")
    autocomplete_fields = ("author",)


class RetrievalRunAdmin(admin.ModelAdmin):
    list_display = ("title", "ir_task", "date")
    search_fields = ("title", "description", "ir_task__title")
    date_hierarchy = "date"
    ordering = ("-date",)
    readonly_fields = ("id", "date")
    autocomplete_fields = ("ir_task", "reports")


admin.site.register(Report, ReportAdmin)
admin.site.register(AnalysisResult, AnalysisResultAdmin)
admin.site.register(RetrievalTask, RetrievalTaskAdmin)
admin.site.register(RetrievalRun, RetrievalRunAdmin)
