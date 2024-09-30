from django.contrib import admin

from . import models


class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['rest_api_url']


class AggregatedDataAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'agg_method']


class AggregatedDataHistoryAdmin(admin.ModelAdmin):
    list_display = ['agg_datasource', 'timestamp', 'value']


admin.site.register(models.DataSource, DataSourceAdmin)
admin.site.register(models.AggregatedData, AggregatedDataAdmin)
admin.site.register(models.AggregatedDataHistory, AggregatedDataHistoryAdmin)
