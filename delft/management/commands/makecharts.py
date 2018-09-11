'''
Created on Dec 6, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Well
from acacia.meetnet.util import chart_for_well, chart_for_screen
from datetime import datetime
import os
import pytz
from acacia.data.util import slugify

class Command(BaseCommand):
    help = 'maak grafiekjes voor 2017'
    def add_arguments(self, parser):
        parser.add_argument('-d', '--dest',
                action='store',
                dest = 'dest',
                default = '.',
                help = 'destination folder')
        parser.add_argument('-s', '--skip',
                action='store_true',
                dest = 'skip',
                default = False,
                help = 'skip well charts')
                        
    def handle(self, *args, **options):
        folder = options.get('dest')
        skip = options.get('skip')
        tz = pytz.timezone('Etc/GMT-1')
        start=datetime(2017,1,1,tzinfo=tz)
        stop=datetime(2017,12,31,tzinfo=tz)
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        #wells = ['B37E0275','B37E0312','B37E3473','B37E3502','B37E3507']
        #screens = ['B37E0275/001','B37E0312/004','B37E3473/004','B37E3502/001','B37E3507/001']

        #for w in Well.objects.filter(name__in=wells):
        for w in Well.objects.all():
            if not skip:
                data = chart_for_well(w)
                filename = os.path.join(folder,w.nitg + '.png')
                print filename
                with open(filename,'wb') as png:
                    png.write(data)

            for s in w.screen_set.all():
                name = unicode(s)
                #if name in screens:
                data = chart_for_screen(s,start,stop,loggerpos=False)
                filename = os.path.join(folder,slugify(name) + '.png')
                print filename
                with open(filename,'wb') as png:
                    png.write(data)
            