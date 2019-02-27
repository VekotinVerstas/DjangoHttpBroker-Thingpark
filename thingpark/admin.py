from django.contrib import admin
from .models import Datalogger, DataloggerForward


class ForwardInline(admin.StackedInline):
    model = DataloggerForward
    extra = 1


class DataloggerAdmin(admin.ModelAdmin):
    inlines = [ForwardInline]
    list_display = ('devid', 'name', 'activity_at', 'created_at')


admin.site.register(Datalogger, DataloggerAdmin)
