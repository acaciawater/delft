'''
Created on Dec 6, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from optparse import make_option
from acacia.data.models import Series
    
def outliers(series):
    data = series.to_pandas()
    stats = data.describe()
    std = stats['std']
    mean = stats['mean']
    x1 = mean - 3 * std
    x2 = mean + 3 * std;
    below = data[data<x1]
    above = data[data>x2]
    return (below,above)
            
class Command(BaseCommand):
    args = ''
    help = 'Test on outliers'
    option_list = BaseCommand.option_list + (
            make_option('--delete',
                action='store_true',
                dest = 'delete',
                default = False),
        )
        
    def handle(self, *args, **options):
        for s in Series.objects.filter(name__endswith='COMP'):
            b,a = outliers(s)
            if not b.empty and b.size < 2: # pnly below and single outliers
                print s, b
                ans = raw_input('Delete? (y/n)')
                if ans.startswith('y'):
                    date = b.index[0]
                    point = s.datapoints.get(date=date)
                    print 'Deleting', point.date, point.value
                    point.delete()
                    print 'Done'