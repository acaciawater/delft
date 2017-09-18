'''
Created on Dec 6, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.data.models import Series
import pandas as pd
from django.utils.text import slugify

class Command(BaseCommand):
    args = ''
    help = 'Vergelijk metingen met wareco telemetrie'
                        
    def handle(self, *args, **options):
        for warecoseries in Series.objects.filter(parameter__datasource__name__startswith='Wareco'):
            wareco = warecoseries.to_pandas()
            warecostart = wareco.index[0]
            warecostop = wareco.index[-1]
            loc = warecoseries.meetlocatie()
            for pzhseries in loc.series_set.filter(name__endswith='COMP'):
                print loc.name
                pzh = pzhseries.to_pandas()
                pzhstart = pzh.index[0]
                pzhstop = pzh.index[-1]
                start = max(warecostart,pzhstart)
                stop = min(warecostop,pzhstop)
                if start < stop:
                    # align both series
                    wareco, pzh = wareco.align(pzh)
                    pzh = pzh[start:stop].interpolate(method='time')
                    wareco = wareco[start:stop].interpolate(method='time')
                    verschil = wareco - pzh
                    name = unicode(loc.name)
                    df = pd.DataFrame({'filter': name, 'pzh': pzh, 'wareco': wareco, 'verschil_cm': verschil*100})
                    df['abs_verschil_cm'] = abs(df['verschil_cm'])
                    df.dropna(inplace=True)
                    stats = df.describe()
                    print stats
                    df.to_csv('verschil_{}.csv'.format(slugify(name)))
                