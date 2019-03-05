'''
Created on Jul 20, 2017

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Screen
import datetime
import pandas as pd

class Command(BaseCommand):
    args = ''
    help = 'maakt dump voor olivier'
                        
    def add_arguments(self, parser):
        parser.add_argument('-b', '--begin',
                action='store',
                dest = 'begin',
                default = 2013,
                help = 'first year')

        parser.add_argument('-e', '--end',
                action='store',
                dest = 'end',
                default = 2018,
                help = 'last year')

    def handle(self, *args, **options):
        first = datetime.date(int(options.get('begin')),1,1)
        last = datetime.date(int(options.get('end'))+1,1,1)
        df = pd.DataFrame() 
        for s in Screen.objects.order_by('well','nr'):
            print(s)
            series = s.get_compensated_series(start=first,stop=last)
            try:
                series = series.resample('H').nearest()
                df[s] = series
            except:
                pass
        df.to_csv('olivier.csv')