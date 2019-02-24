from django.contrib import admin
from .models import Datalogger


class DataloggerAdmin(admin.ModelAdmin):
    list_display = ('devid', 'name', 'activity_at', 'created_at')


admin.site.register(Datalogger, DataloggerAdmin)
