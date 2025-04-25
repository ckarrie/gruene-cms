from cms.models import Page
from django.db.models import Min, Max
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.apps import apps

from gruene_cms.forms import NewstickerFilterForm
from gruene_cms.models import NewsItem
from gruene_cms.views.base import AppHookConfigMixin
from icalendar import Calendar, Event
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.template import defaultfilters


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

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            get_short = request.GET.get('s', None)
            short_obj = apps.get_model('newsticker.ShareLink').objects.filter(short=get_short, valid_until__gte=timezone.now())
            if not short_obj.exists():
                login_url = reverse('gruene_cms_dashboard:db_login')
                login_page_param = '?next=' + reverse('gruene_cms_news:newsticker_index') + '&code=share'
                return HttpResponseRedirect(login_url + login_page_param)
        return super(NewsTickerView, self).get(request, *args, **kwargs)

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

        # short link
        short_link_obj = None
        short_link_get = self.request.GET.get('s', None)
        if short_link_get:
            short_link_obj = apps.get_model('newsticker.ShareLink').objects.filter(short=short_link_get).first()
            # commented this out, we only want to track real shortlink clicks
            # if short_link_obj:
            #    short_link_obj.add_request(self.request)

        filter_form_has_errors = len(filter_form.errors) > 0
        newsitems = apps.get_model('newsticker.TickerItem').objects.current(ref_date=ref_date, limit_days=limit_days)
        newsitems_by_date = apps.get_model('newsticker.TickerItem').objects.current_by_date(qs=newsitems, short_link=short_link_obj)

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

        existing_shortlinks = apps.get_model('newsticker.ShareLink').objects.filter(valid_until__gte=timezone.now())
        for sl in existing_shortlinks:
            sl.share_link = self.request.build_absolute_uri(sl.get_short_link_url())

        shortlink_options_qd = QueryDict('', mutable=True)
        share_link_valid_until = timezone.now() + timezone.timedelta(days=7)
        shortlink_options = {
            'display_days': str(limit_days),
            'display_date': defaultfilters.date(ref_date, "SHORT_DATE_FORMAT"),  # ref_date.strftime("%Y-%m-%d"),
            # 'valid_until': defaultfilters.date(share_link_valid_until, "SHORT_DATETIME_FORMAT")
            # 'valid_until': share_link_valid_until.strftime("%Y-%m-%dT%H:%M:%S%z"),
            # 'valid_until_0': share_link_valid_until.strftime("%Y-%m-%d"),
            # 'valid_until_1': share_link_valid_until.strftime("%H:%M:%S"),
        }
        shortlink_options_qd.update(shortlink_options)

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
            'max_dt': max_dt,
            'shortlink': short_link_obj,
            'existing_shortlinks': existing_shortlinks,
            'shortlink_options_qd': shortlink_options_qd,
            'shortlink_options': shortlink_options,

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


class NewsTickerShareLinkView(AppHookConfigMixin, generic.RedirectView):
    #url = reverse('gruene_cms_news:newsticker_index')
    permanent = False

    def get(self, request, *args, **kwargs):
        get_short = kwargs.get('short', None)
        login_url = reverse('gruene_cms_dashboard:db_login')
        login_page_param = '?next=' + reverse('gruene_cms_news:newsticker_index') + '&code=share'
        self.url = login_url + login_page_param
        if get_short:
            short_obj = apps.get_model('newsticker.ShareLink').objects.filter(short=get_short, valid_until__gte=timezone.now()).first()
            if short_obj:
                self.url = short_obj.resolve_url()
                short_obj.add_request(request)

        return super(NewsTickerShareLinkView, self).get(request, *args, **kwargs)



