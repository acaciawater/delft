'''
Created on Dec 6, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.data.models import Series, ManualSeries
import pandas as pd

class Command(BaseCommand):
    args = ''
    help = 'Vergelijk standen en handpeilingen'
                        
    def handle(self, *args, **options):
        dfall = None
        for h in ManualSeries.objects.all():
            hand = h.to_pandas()
            mloc = h.meetlocatie()
            print mloc
            try:
                name = '%s COMP' % mloc.name
                ser = Series.objects.get(name = name)
                try:
                    if ser.mlocatie != mloc:
                        ser.mlocatie = mloc
                        ser.save()
                except Exception as e:
                    print e
                    continue
            except Series.DoesNotExist:
                print 'Series', name, 'not found' 
                continue
            
            data = ser.to_pandas()

            left,right=data.align(hand)
            data = left.interpolate(method='time')
            data = data.reindex(hand.index)
            verschil = data - hand
            df = pd.DataFrame({'locatie': str(mloc), 'data': data, 'hand': hand, 'verschil': verschil})
            df.dropna(inplace=True)

            if dfall is None:
                dfall = df
            else:
                dfall = dfall.append(df)
            dfall.to_csv('diff.csv')
            