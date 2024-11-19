from django.urls import reverse
from django.views import generic
from django.db.models import Q
from gruene_cms.forms import SearchForm
from gruene_cms.views.base import AppHookConfigMixin
from gruene_cms.models import NewsItem, CalendarItem


class SearchView(AppHookConfigMixin, generic.FormView):
    form_class = SearchForm
    template_name = 'gruene_cms/apps/search.html'

    def form_valid(self, form):
        return self.form_invalid(form=form)

    def get_context_data(self, **kwargs):
        ctx = super(SearchView, self).get_context_data(**kwargs)

        form = ctx['form']
        if form.is_valid():
            q = form.cleaned_data.get('q')
            news_qs = NewsItem.objects.filter(
                Q(title__icontains=q) |
                Q(subtitle__icontains=q) |
                Q(keywords__iexact=q) |
                Q(summary__icontains=q) |
                Q(content__icontains=q),
                categories__is_public=True
            )

            news_qs = news_qs.order_by('-published_from').distinct()

            for news in news_qs:
                if news.newsfeedreader_external_link:
                    news.detail_link = news.newsfeedreader_external_link
                else:
                    news.detail_link = reverse('gruene_cms_news:detail', kwargs={'slug': news.slug})

            cal_qs = CalendarItem.objects.filter(
                title__icontains=q
            )

            for cal in cal_qs:
                if cal.linked_page:
                    cal.linked_url = cal.linked_page.get_absolute_url()
                if cal.linked_news:
                    cal.linked_url = reverse('gruene_cms_news:detail', kwargs={'slug': cal.linked_news.slug})

            ctx.update({
                'news_qs': news_qs,
                'cal_qs': cal_qs,
                'has_results': any([
                    news_qs.exists(),
                    cal_qs.exists(),
                ])
            })

        return ctx


    #def get_form_kwargs(self):
    #    q = self.request.GET.get('q')
    #    initials = super(SearchView, self).get_form_kwargs()
    #    initials[q] = q
    #    return initials