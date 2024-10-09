from django.views import generic
from menus.base import Menu
from gruene_cms.models import NewsItem
from gruene_cms.views.base import AppHookConfigMixin


class NewsDetailView(AppHookConfigMixin, generic.DetailView):
    model = NewsItem
    template_name = 'gruene_cms/apps/news/details.html'
    cms_page = None

    def get_context_data(self, **kwargs):
        ctx = super(NewsDetailView, self).get_context_data(**kwargs)
        ctx.update({
            'current_page': self.cms_page,
            'ancestors': Menu
        })
        #print(ctx)
        #print(self.cms_page)
        return ctx

    def get_paginate_by(self, queryset):
        try:
            return self.config.paginate_by
        except AttributeError:
            return 10
