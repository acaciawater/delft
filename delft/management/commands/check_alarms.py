from django.core.management.base import BaseCommand
from acacia.data.models import Series
from django.utils import timezone
from django.db.models.aggregates import Count
import logging
from datetime import timedelta
from acacia.meetnet.actions import make_wellcharts
from acacia.meetnet.models import Well
logger = logging.getLogger(__name__)
            
class Command(BaseCommand):
    help = 'Controleer op alarm en verstuur emails'

    def add_arguments(self, parser):
        parser.add_argument('-n','--notify',
                action = 'store_true',
                dest = 'notify',
                help = 'Notify receivers by email'
        )
        parser.add_argument('-d','--download',
                action = 'store_true',
                dest = 'download',
                help = 'Download new data before checks'
        )
        parser.add_argument('-s','--start',
                dest = 'start',
                help = 'starting time for checking alarm conditions (default=24 hours ago)'
        )

    def download_and_update(self, series):
        try:
            ds = series.datasource()
            if ds.download():
                data = ds.get_data(start=series.tot())
                if series.update(data=data):
                    well = Well.objects.get(name=series.projectlocatie().name)
                    make_wellcharts(None,None,[well])
        except Exception as e:
            logger.error(e)
                
    def handle(self, *args, **options):
        download = options.get('download')
        notify = options.get('notify')
        now = timezone.now().replace(minute=0,second=0,microsecond=0)
        start = options.get('start')
        if not start:
            start=now-timedelta(hours=24)
        # select series with alarms
        queryset = Series.objects.annotate(alarm_count=Count('alarm')).filter(alarm_count__gt=0)
        logger.debug('checking {} time series for alarms'.format(queryset.count()))
        count = 0
        for series in queryset:
            if download:
                self.download_and_update(series)
            for alarm in series.alarm_set.filter(active=True):
                events = alarm.inspect(notify=notify,start=start,stop=now)
                if events:
                    num_events = len(events)
                    count += num_events
                    logger.info('alarm {}: {} new events occurred.'.format(alarm,num_events))
        logger.debug('Done, {} new events.'.format(count))
        