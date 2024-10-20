from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, UserManager
from cms import api as cms_api
from cms.utils.permissions import set_current_user

from gruene_cms.cms_apps import DashboardApphook, NewsPageApphook
from gruene_cms.models import NewsPageConfig
from djangocms_versioning.models import Version


PAGE_HOME_ID = "home"
PAGE_NEWS_ID = "aktuelles"
PAGE_DASHBOARD_ID = "dashboard"
LANG = 'de'

"""
References:
- djangoCMS API: https://docs.django-cms.org/en/latest/reference/api_references.html
"""

class Command(BaseCommand):
    help = "Creates basic gruenen cms"

    def handle(self, *args, **options):
        # set current threads user
        user = User.objects.create_superuser(
            username='changeme',
            email='change@me.com',
            password='changeme!'
        )

        self.stdout.write(
            self.style.NOTICE(f'Using user {user}')
        )

        home_page = cms_api.create_page(
            title="Startseite",
            template="gruene_v1.html",
            language=LANG,
            menu_title="Home",
            slug="home",
            apphook=None,
            created_by=user,
            parent=None,
            publication_date=None,
            publication_end_date=None,
            in_navigation=True, soft_root=False,
            reverse_id=PAGE_HOME_ID,
            published=None,
            site=None,
            login_required=False,
            position="last-child"
        )

        co = home_page.get_content_obj(language=LANG, fallback=False, force_reload=True)
        print("co", co)
        v_home = Version.objects.get_for_content(home_page)
        v_home.publish(user=user)

        self.stdout.write(
            self.style.SUCCESS(f'Created Page {home_page.get_page_title()} id={home_page.pk}')
        )

        # Aktuelles
        news_apphock_config = NewsPageConfig(namespace=PAGE_NEWS_ID).save()
        news_apphook  = NewsPageApphook()
        news_apphook.app_config = news_apphock_config
        news_page = cms_api.create_page(
            title="Aktuelles",
            template="gruene_v1.html",
            language=LANG,
            menu_title="Aktuelles",
            slug=PAGE_NEWS_ID,
            apphook=news_apphook,
            apphook_namespace=PAGE_NEWS_ID,
            created_by=user,
            parent=home_page,
            publication_date=None,
            publication_end_date=None,
            in_navigation=True, soft_root=False,
            reverse_id=PAGE_NEWS_ID,
            published=None,
            site=None,
            login_required=False,
            position="last-child"
        )

        self.stdout.write(
            self.style.SUCCESS(f'Created Page {news_page.get_page_title()} id={news_page.pk}')
        )

        # Dashboard
        
        dashboard_apphook  = DashboardApphook()
        dashboard_page = cms_api.create_page(
            title="Dashboard",
            template="gruene_v1.html",
            language=LANG,
            menu_title="Dashboard",
            slug=PAGE_DASHBOARD_ID,
            apphook=dashboard_apphook,
            apphook_namespace=PAGE_DASHBOARD_ID,
            created_by=user,
            parent=home_page,
            publication_date=None,
            publication_end_date=None,
            in_navigation=True, soft_root=False,
            reverse_id=PAGE_DASHBOARD_ID,
            published=None,
            site=None,
            login_required=False,
            position="last-child"
        )

        self.stdout.write(
            self.style.SUCCESS(f'Created Page {dashboard_page.get_page_title()} id={dashboard_page.pk}')
        )

        cms_api.add_plugin("content")


