from django.views import generic
from menus.base import Menu
from gruene_cms.models import NewsItem
from gruene_cms.views.base import AppHookConfigMixin


class NewsDetailView(AppHookConfigMixin, generic.DetailView):
    model = NewsItem
    template_name = 'gruene_cms/apps/news/details.html'

    def get_paginate_by(self, queryset):
        try:
            return self.config.paginate_by
        except AttributeError:
            return 10
