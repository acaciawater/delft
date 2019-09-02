import os

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from acacia.meetnet.models import Screen

class Command(BaseCommand):
    args = ''
    help = 'Export all series'
        
    fldr = './export'
    

    def handle(self, *args, **options):
        if not os.path.exists(self.fldr):
            os.makedirs(self.fldr)
        for s in Screen.objects.all():
            name = slugify(s)
            fname = os.path.join(self.fldr,name) + '.csv'
            print fname
            with open(fname,'w') as f:
                f.write('Datum,{}\n'.format(s))
                for p in s.find_series().datapoints.all():
                    f.write('{},{}\n'.format(p.date,p.value))
                
