from django.utils import timezone
from django.views import generic
from menus.base import Menu
from gruene_cms.models import NewsItem
from gruene_cms.views.base import AppHookConfigMixin


class NewsDetailView(AppHookConfigMixin, generic.DetailView):
    model = NewsItem
    template_name = 'gruene_cms/apps/news/details.html'

    def get_queryset(self):
        qs = super(NewsDetailView, self).get_queryset().filter()
        if not self.request.user.is_staff:
            qs = qs.filter(published_from__lte=timezone.now())
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(NewsDetailView, self).get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx['prev_object'] = qs.filter(
            published_from__lt=self.object.published_from,
            #newsfeedreader_source__isnull=True
        ).order_by('-published_from').first()

        ctx['next_object'] = qs.filter(
            published_from__gt=self.object.published_from
        ).order_by('published_from').first()
        return ctx

    def get_paginate_by(self, queryset):
        try:
            return self.config.paginate_by
        except AttributeError:
            return 10
