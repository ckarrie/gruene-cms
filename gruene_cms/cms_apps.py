from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.core.exceptions import ObjectDoesNotExist
from django.urls import path, reverse
from gruene_cms.views import news as news_views, dashboard as dashboard_views
from gruene_cms.models import NewsPageConfig


class NewsPageApphook(CMSApp):
    app_name = "gruene_cms_news"
    name = "GrueneCMS News"
    app_config = NewsPageConfig

    def get_urls(self, page=None, language=None, **kwargs):
        return [
            path('<str:slug>/', news_views.NewsDetailView.as_view(cms_page=page), name="detail"),
            path('<str:slug>/ical/', news_views.DownloadICSView.as_view(), name="download_ics"),
        ]

    def get_configs(self):
        return self.app_config.objects.all()

    def get_config(self, namespace):
        try:
            return self.app_config.objects.get(namespace=namespace)
        except ObjectDoesNotExist:
            return None

    def get_config_add_url(self):
        try:
            return reverse("admin:{}_{}_add".format(self.app_config._meta.app_label, self.app_config._meta.model_name))
        except AttributeError:
            return reverse(
                "admin:{}_{}_add".format(self.app_config._meta.app_label, self.app_config._meta.module_name)
            )


class DashboardApphook(CMSApp):
    app_name = "gruene_cms_dashboard"
    name = "GrueneCMS Dashboard"

    def get_urls(self, page=None, language=None, **kwargs):
        return [
            # tasks
            path('tasks/add/', dashboard_views.TaskCreateView.as_view(cms_page=page), name="task_add"),
            path('tasks/<int:pk>/', dashboard_views.TaskEditView.as_view(cms_page=page), name="task_edit"),
            path('tasks/', dashboard_views.TaskListView.as_view(cms_page=page), name="task_list"),
            path('webdav/<int:pk>/view_file/', dashboard_views.WebDAVViewLocalFileView.as_view(cms_page=page), name="webdav_view_local_file"),
            path('webdav/<int:pk>/serve_file/', dashboard_views.WebDAVServeLocalFileView.as_view(cms_page=page), name="webdav_serve_local_file"),
        ]


apphook_pool.register(NewsPageApphook)
apphook_pool.register(DashboardApphook)
