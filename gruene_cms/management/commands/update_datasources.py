from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from gruene_cms.models import AggregatedData, AggregatedDataHistory, NewsFeedReader, WebDAVClient


class Command(BaseCommand):
    help = "Updates Data from DataSources and removes old statistics"

    def handle(self, *args, **options):
        # datasources
        for ad in AggregatedData.objects.all():
            ad.aggregate_datasources(limit_enable_for_auto_update=True)

        self.stdout.write(
            self.style.SUCCESS('Updated DataSources')
        )

        # news feed
        for nf in NewsFeedReader.objects.filter(enable_for_auto_update=True):
            nf.fetch_feed()
        self.stdout.write(
            self.style.SUCCESS('Updated NewsFeedReaders')
        )

        # webdav clients
        for wc in WebDAVClient.objects.filter(enable_for_auto_update=True):
            wc.sync_folder()
        self.stdout.write(
            self.style.SUCCESS('Updated WebDAVClients')
        )


        # cleanup
        two_days_ago = timezone.now() - timezone.timedelta(days=2)
        adh_qs = AggregatedDataHistory.objects.filter(timestamp__lte=two_days_ago)
        adh_qs_cnt = adh_qs.count()
        adh_qs.delete()

        self.stdout.write(
            self.style.SUCCESS(f'Removed {adh_qs_cnt} obsolete AggregatedDataHistory objects')
        )


