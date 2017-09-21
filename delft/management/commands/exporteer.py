import os

from django.core.management.base import BaseCommand
from acacia.data.models import Series
from django.utils.text import slugify

class Command(BaseCommand):
    args = ''
    help = 'Export all series'
        
    fldr = './export'
    

    def handle(self, *args, **options):
        screens = ['B37E0275/001','B37E0312/004','B37E3473/004','B37E3502/001','B37E3507/001']
        if not os.path.exists(self.fldr):
            os.makedirs(self.fldr)
        for s in Series.objects.all():
            loc = s.meetlocatie()
            if not loc or not loc.name in screens:
                continue
            if s.parameter:
                name = unicode(s.parameter)
            else: 
                name = s.name
            name = slugify(name)
            fname = os.path.join(self.fldr,name) + '.csv'
            print fname
            with open(fname,'w') as f:
                text = s.to_csv()
                f.write(text)
                
