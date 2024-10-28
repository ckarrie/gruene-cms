from django.utils import timezone
from django.views import generic
from menus.base import Menu
from gruene_cms.models import NewsItem
from gruene_cms.views.base import AppHookConfigMixin
from icalendar import Calendar, Event
from django.contrib.sites.models import Site
from django.http import HttpResponse


class NewsDetailView(AppHookConfigMixin, generic.DetailView):
    model = NewsItem
    template_name = 'gruene_cms/apps/news/details.html'

    def get_queryset(self):
        qs = super(NewsDetailView, self).get_queryset().filter(
            newsfeedreader_source__isnull=True,
            categories__is_public=True
        )
        if not self.request.user.is_staff:
            qs = qs.filter(published_from__lte=timezone.now())
        qs = qs.distinct()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(NewsDetailView, self).get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx['prev_object'] = qs.filter(
            published_from__lt=self.object.published_from,
            #newsfeedreader_source__isnull=True
        ).order_by('-published_from').first()

        ctx['next_object'] = qs.filter(
            published_from__gt=self.object.published_from,
            #newsfeedreader_source__isnull=True
        ).order_by('published_from').first()
        return ctx

    def get_paginate_by(self, queryset):
        try:
            return self.config.paginate_by
        except AttributeError:
            return 10


class DownloadICSView(NewsDetailView):

    def render_to_response(self, context, **response_kwargs):
        cal = Calendar()
        site = Site.objects.get_current()
        cal.add('prodid', '-//%s Events Calendar//%s//' % (site.name, site.domain))
        cal.add('version', '2.0')

        site_token = site.domain.split('.')
        site_token.reverse()
        site_token = '.'.join(site_token)

        for event in self.object.get_related_objects()['calendar_items']:
            ical_event = Event()
            ical_event.add('summary', event.title)
            ical_event.add('dtstart', event.dt_from)
            ical_event.add('dtend', event.dt_until and event.dt_until or event.dt_from)
            ical_event.add('dtstamp', event.dt_until and event.dt_until or event.dt_from)
            ical_event['uid'] = '%d.event.events.%s' % (event.pk, site_token)
            cal.add_component(ical_event)

        response = HttpResponse(cal.to_ical(), content_type="text/calendar")
        response['Content-Disposition'] = 'attachment; filename=%s.ics' % self.object.slug
        return response