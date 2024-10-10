from django.core.management.base import BaseCommand, CommandError
from cms import api as cms_api


PAGE_HOME_ID = "home"
PAGE_NEWS_ID = "aktuelles"
PAGE_DASHBOARD_ID = "dashboard"


class Command(BaseCommand):
    help = "Creates basic gruenen cms"

    def handle(self, *args, **options):
        home_page = cms_api.create_page(
            title="Startseite",
            template="gruene_v1.html",
            language="de",
            menu_title="Home",
            slug="home",
            apphook=None,
            created_by='python-api',
            parent=None,
            publication_date=None,
            publication_end_date=None,
            in_navigation=False, soft_root=False,
            reverse_id=PAGE_HOME_ID,
            published=None,
            site=None,
            login_required=False,
            position="last-child"
        )

        cms_api.add_plugin(

        )



