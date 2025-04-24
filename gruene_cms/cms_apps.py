from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.core.exceptions import ObjectDoesNotExist
from django.urls import path, reverse
from django.contrib.auth.views import LogoutView, PasswordChangeView
from gruene_cms.views import news as news_views, dashboard as dashboard_views, search as search_views
from gruene_cms.models import NewsPageConfig


class NewsPageApphook(CMSApp):
    app_name = "gruene_cms_news"
    name = "GrueneCMS News"
    app_config = NewsPageConfig

    def get_urls(self, page=None, language=None, **kwargs):
        return [
            path('newsticker/', news_views.NewsTickerView.as_view(), name="newsticker_index"),
            path('newsticker/s/<str:short>', news_views.NewsTickerShareLinkView.as_view(), name="newsticker_share"),
            #path('newsticker/share/<slug>/', news_views.NewsTickerShareView.as_view(), name="newsticker_index"),

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
            # webdav
            path('webdav/<int:pk>/view_file/', dashboard_views.WebDAVViewLocalFileView.as_view(cms_page=page), name="webdav_view_local_file"),
            path('webdav/<int:pk>/serve_file/', dashboard_views.WebDAVServeLocalFileView.as_view(cms_page=page), name="webdav_serve_local_file"),
            path('webdav/<int:pk>/upload_file/', dashboard_views.WebDAVUploadView.as_view(cms_page=page), name="webdav_upload_file"),
            # cal
            path('cal/add/', dashboard_views.CalendarItemCreateView.as_view(cms_page=page), name="calendaritem_add"),
            # auth/user
            path('logout/', LogoutView.as_view(), name="db_logout"),
            path('change-password/', PasswordChangeView.as_view(), name="db_pwchange"),
        ]


class SearchApphook(CMSApp):
    app_name = 'gruene_cms_search'
    name = 'GrueneCMS Search'

    def get_urls(self, page=None, language=None, **kwargs):
        from django.conf.urls.i18n import i18n_patterns
        urls = [
            path('', search_views.SearchView.as_view(cms_page=page), name='search'),
        ]

        return urls


apphook_pool.register(NewsPageApphook)
apphook_pool.register(DashboardApphook)
apphook_pool.register(SearchApphook)
