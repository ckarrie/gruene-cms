from django.contrib import admin

from . import models


class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['rest_api_url']


class AggregatedDataAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'agg_method']


class AggregatedDataHistoryAdmin(admin.ModelAdmin):
    list_display = ['agg_datasource', 'timestamp', 'value']


class CalendarAdmin(admin.ModelAdmin):
    list_display = ['title']


class CalendarItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'calendar', 'subtitle', 'dt_from', 'dt_until', 'location']
    list_filter = ['calendar']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title']


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ['title']


# datasources
admin.site.register(models.DataSource, DataSourceAdmin)
admin.site.register(models.AggregatedData, AggregatedDataAdmin)
admin.site.register(models.AggregatedDataHistory, AggregatedDataHistoryAdmin)

# calendar
admin.site.register(models.Calendar, CalendarAdmin)
admin.site.register(models.CalendarItem, CalendarItemAdmin)

# news
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.NewsItem, NewsItemAdmin)
