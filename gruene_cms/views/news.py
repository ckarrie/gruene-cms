from cms.models import Page
from django.db.models import Min, Max
from django.utils import timezone
from django.views import generic
from django.apps import apps
from menus.base import Menu

from gruene_cms.forms import NewstickerFilterForm
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
        )
        if not self.request.user.is_staff:
            qs = qs.filter(
                published_from__lte=timezone.now(),
                categories__is_public=True
            )
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


class NewsTickerView(AppHookConfigMixin, generic.TemplateView):
    template_name = 'gruene_cms/apps/newsticker/newsticker_index.html'

    def get_context_data(self, **kwargs):
        ctx = super(NewsTickerView, self).get_context_data(**kwargs)
        limit_days = 3
        max_limit_days = 10
        collapse_cat = None
        show_all = True
        filter_date = None
        ref_date = timezone.now().date()

        if not self.request.GET.get('days', None):
            filter_form = NewstickerFilterForm(initial={
                'date': timezone.now().date(),
                'days': 1,
                'show_all': True
            })
        else:
            filter_form = NewstickerFilterForm(data=self.request.GET)

        if filter_form.is_valid():
            ff_cd = filter_form.cleaned_data
            limit_days = min(int(ff_cd['days'] or '0'), max_limit_days)
            show_all = ff_cd['show_all']
            collapse_cat = ff_cd['collapse_cat']
            ref_date = ff_cd['date']

        filter_form_has_errors = len(filter_form.errors) > 0
        newsitems = apps.get_model('newsticker.TickerItem').objects.current(ref_date=ref_date, limit_days=limit_days)
        newsitems_by_date = apps.get_model('newsticker.TickerItem').objects.current_by_date(qs=newsitems)

        qs_aggregations = newsitems.aggregate(min_dt=Min('pub_dt'), max_dt=Max('pub_dt'))
        min_dt = timezone.localtime(qs_aggregations['min_dt'], timezone=timezone.get_current_timezone())
        max_dt = timezone.localtime(qs_aggregations['max_dt'], timezone=timezone.get_current_timezone())
        min_max_dt_equal_day = min_dt.date() == max_dt.date()

        # vars
        start_day = timezone.localtime(
            timezone.now() - timezone.timedelta(days=limit_days),
            timezone=timezone.get_current_timezone()
        ).date()
        today = timezone.localtime(timezone.now(), timezone=timezone.get_current_timezone()).date()
        ctx.update({
            'newsitems_by_date': newsitems_by_date,
            'today': today,
            'start_day': start_day,
            'now': timezone.now(),
            'min_max_dt_equal_day': min_max_dt_equal_day,
            # fixing "Ein Templatetag konnte die Seite `{'reverse_id': ''}` nicht finden:
            'current_page': self.cms_page or Page.objects.get_home(),
            'show_all': show_all,
            'collapse_cat': collapse_cat,
            'filter_form': filter_form,
            'filter_form_has_errors': filter_form_has_errors,
            'min_dt': min_dt,
            'max_dt': max_dt
        })
        return ctx


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