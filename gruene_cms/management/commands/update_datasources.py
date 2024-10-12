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
        nf_qs = NewsFeedReader.objects.filter(enable_for_auto_update=True)
        for nf in nf_qs:
            nf.fetch_feed()
        self.stdout.write(
            self.style.SUCCESS(f'Updated {nf_qs.count()} NewsFeedReaders')
        )

        # webdav clients
        wc_qs = WebDAVClient.objects.filter(enable_for_auto_update=True)
        for wc in wc_qs:
            wc.sync_folder()
        self.stdout.write(
            self.style.SUCCESS(f'Updated {wc_qs.count()} WebDAVClients')
        )

        # cleanup
        two_days_ago = timezone.now() - timezone.timedelta(days=2)
        adh_qs = AggregatedDataHistory.objects.filter(timestamp__lte=two_days_ago)
        adh_qs_cnt = adh_qs.count()
        adh_qs.delete()

        self.stdout.write(
            self.style.SUCCESS(f'Removed {adh_qs_cnt} obsolete AggregatedDataHistory objects')
        )


