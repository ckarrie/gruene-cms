from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.views.generic.base import TemplateView
from django.contrib.sites.models import Site
from cms.sitemaps import CMSSitemap
from cms.utils import get_current_site
from cms.utils.i18n import get_public_languages
from cms.models import PageContent, PageUrl
from django.contrib.sitemaps import Sitemap
from gruene_cms.models import NewsItem


class RobotsTxtView(TemplateView):
    template_name = 'gruene_cms/robots.txt'
    content_type = 'text/plain'

    def get_context_data(self, **kwargs):
        ctx = super(RobotsTxtView, self).get_context_data(**kwargs)
        site = get_current_site()
        languages = get_public_languages(site_id=site.pk)
        try:
            sitemap_url = reverse('seo_sitemapxml')
            news_sitemap_url = reverse('seo_newssitemapxml')
        except NoReverseMatch:
            sitemap_url = ''
            news_sitemap_url = ''
            print("ERROR: missing seo_sitemapxml/seo_newssitemapxml in root_urlconf, see docs/setup.md for an example")

        # internal pages
        disallow_urls = []
        reverse_ids = ['dashboard']
        cms_pages = PageUrl.objects.get_for_site(site).filter(language__in=languages, path__isnull=False, page__login_required=False)
        dashboard_pages = cms_pages.filter(page__reverse_id__in=reverse_ids)
        disallow_urls += [page_url.get_absolute_url(page_url.language) for page_url in dashboard_pages]

        ctx.update({
            'host': site.domain,
            'sitemap_url': sitemap_url,
            'news_sitemap_url': news_sitemap_url,
            'disallow_urls': disallow_urls
        })
        return ctx


class GoogleSearchConsoleView(TemplateView):
    template_name = 'gruene_cms/google_search_console.html'


class GrueneCMSSitemap(CMSSitemap):
    changefreq = 'daily'


class NewsSitemap(Sitemap):
    languages = ['de']
    changefreq = 'daily'

    def items(self):
        now = timezone.now()
        qs = NewsItem.objects.filter(
            categories__is_public=True,
            published_from__lte=now,
            #published_until__gte=now,
            newsfeedreader_external_link__isnull=True
        )
        return qs

    def lastmod(self, obj):
        return obj.published_from

    def location(self, item):
        return reverse('gruene_cms_news:detail', kwargs={'slug': item.slug})





