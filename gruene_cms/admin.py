from django.contrib import admin, messages
from django.templatetags.tz import localtime
from django.utils.translation import gettext_lazy as _

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
    list_display = ['title', 'calendar', 'subtitle', 'dt_from', 'dt_until', 'location', 'is_active', 'is_past']
    list_filter = ['calendar']

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['linked_page'].queryset = context['adminform'].form.fields['linked_page'].queryset.filter(pagecontent_set__isnull=False).distinct()
        context['adminform'].form.fields['linked_news'].queryset = context['adminform'].form.fields['linked_news'].queryset.filter(newsfeedreader_source__isnull=True).order_by('-published_from').distinct()
        context['adminform'].form.fields['linked_news'].label_from_instance = lambda obj: "%s %s" % (localtime(obj.published_from), obj.title)

        return super(CalendarItemAdmin, self).render_change_form(request, context, *args, **kwargs)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title']
    prepopulated_fields = {"slug": ("title",)}


class NewsImageInlineAdmin(admin.TabularInline):
    model = models.NewsImage


class NewsAttachmentInlineAdmin(admin.TabularInline):
    model = models.NewsAttachment


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'published_from', 'newsfeedreader_source']
    list_filter = ['newsfeedreader_source']
    inlines = [NewsImageInlineAdmin, NewsAttachmentInlineAdmin]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ['title', 'subtitle']


class NewsImageAdmin(admin.ModelAdmin):
    list_display = ['title']


class NewsFeedReaderAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'category', 'last_updated', 'author_user', 'enable_for_auto_update', 'active_auto_update']
    actions = ['fetch_feeds']

    @admin.action(description=_('Fetch selected feeds'))
    def fetch_feeds(self, request, queryset):
        for obj in queryset:
            obj.fetch_feed()
            self.message_user(request, f"Feed updated for {obj.title}", messages.SUCCESS)


class NewsPageConfigAdmin(admin.ModelAdmin):
    pass


# tasks
class TaskItemAdmin(admin.ModelAdmin):
    list_display = ['summary', 'created_at', 'progress', 'category',]
    list_filter = ['category']


class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'comment']


# webdav
class WebDAVClientAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'webdav_hostname', 'entry_path', 'entry_path_title', 'local_path']
    actions = ['sync_folder', 'webdav_download_sync', 'create_filer_objects']

    def sync_folder(self, request, queryset):
        for obj in queryset:
            obj.sync_folder()
            self.message_user(request, f"Sync updated for {obj.title}", messages.SUCCESS)

    @admin.action(description=_("Download from WebDAV (overwrite local)"))
    def webdav_download_sync(self, request, queryset):
        for obj in queryset:
            obj.webdav_download_sync()
            self.message_user(request, f"Download finished for {obj.title}", messages.SUCCESS)

    @admin.action(description=_("Create Filer objects (experimental - do not use!)"))
    def create_filer_objects(self, request, queryset):
        for obj in queryset:
            obj.create_filer_objects()


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
admin.site.register(models.NewsImage, NewsImageAdmin)
admin.site.register(models.NewsFeedReader, NewsFeedReaderAdmin)
admin.site.register(models.NewsPageConfig, NewsPageConfigAdmin)

# tasks
admin.site.register(models.TaskItem, TaskItemAdmin)
admin.site.register(models.TaskComment, TaskCommentAdmin)

#webdav
admin.site.register(models.WebDAVClient, WebDAVClientAdmin)
