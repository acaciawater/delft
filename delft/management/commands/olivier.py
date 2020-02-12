'''
Created on Jul 20, 2017

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Screen
import datetime
import pandas as pd
import pytz

class Command(BaseCommand):
    args = ''
    help = 'maakt dump voor olivier'
                        
    def add_arguments(self, parser):
        parser.add_argument('-c', action='store_true', dest='corrected', default=False, help='Export corrected data (default is raw)')
        parser.add_argument('-b', '--begin',
                action='store',
                dest = 'begin',
                default = 2013,
                help = 'first year')

        parser.add_argument('-e', '--end',
                action='store',
                dest = 'end',
                default = 2019,
                help = 'last year')

    def handle(self, *args, **options):
        tz = pytz.timezone('UTC')
        first = datetime.datetime(int(options.get('begin')),1,1,tzinfo=tz)
        last = datetime.datetime(int(options.get('end'))+1,1,1,tzinfo=tz)
        corr = options.get('corrected')

        df = pd.DataFrame(index=pd.date_range(first,last,freq='H')) 
        for s in Screen.objects.order_by('well','nr'):
            print(s)
            if corr:
                series = s.get_corrected_series(start=first,stop=last)
            else:
                series = s.get_compensated_series(start=first,stop=last)
            if series.any():
                series = series.resample('H').nearest()
                df[s] = series
#         df.to_csv('olivier.csv')
        df.to_excel('olivier.xlsx','sheet1',float_format='%.3f')