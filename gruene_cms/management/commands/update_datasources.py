from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from gruene_cms.models import AggregatedData, AggregatedDataHistory


class Command(BaseCommand):
    help = "Updates Data from DataSources and removes old statistics"

    def handle(self, *args, **options):
        for ad in AggregatedData.objects.all():
            ad.aggregate_datasources()
        self.stdout.write(
            self.style.SUCCESS('Updated DataSources')
        )

        two_days_ago = timezone.now() - timezone.timedelta(days=2)
        adh_qs = AggregatedDataHistory.objects.filter(timestamp__lte=two_days_ago)
        adh_qs_cnt = adh_qs.count()
        adh_qs.delete()

        self.stdout.write(
            self.style.SUCCESS(f'Removed {adh_qs_cnt} obsolete AggregatedDataHistory objects')
        )


