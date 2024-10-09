from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.core.exceptions import ObjectDoesNotExist
from django.urls import path, reverse
from gruene_cms.views import news as news_views
from gruene_cms.models import NewsPageConfig


@apphook_pool.register  # register the application
class NewsPageApphook(CMSApp):
    app_name = "gruene_cms_news"
    name = "GrueneCMS News"
    app_config = NewsPageConfig

    def get_urls(self, page=None, language=None, **kwargs):
        return [
            path('<str:slug>/', news_views.NewsDetailView.as_view(cms_page=page), name="detail"),
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
