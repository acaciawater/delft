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
from django.shortcuts import get_object_or_404

class Command(BaseCommand):
    help = 'maak grafiekjes'
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
                help = 'skip screen charts')

        parser.add_argument('-o', '--owner',
                action='store',
                dest = 'owner',
                default = 'PZH',
                help = 'filter wells by owner')
        
        parser.add_argument('-w', '--well',
                action='store',
                dest = 'well',
                default = False,
                help = 'id of well to make charts for')

        parser.add_argument('-b', '--begin',
                action='store',
                dest = 'begin',
                default = None,
                help = 'first year')

        parser.add_argument('-e', '--end',
                action='store',
                dest = 'end',
                default = None,
                help = 'last year')
                        
    def handle(self, *args, **options):
        folder = options.get('dest')
        noscreen = options.get('skip')
        begin = options.get('begin')
        end = options.get('end')
        tz = pytz.timezone('CET')
        pk = options.get('well')
        owner=options.get('owner')
        start=datetime.datetime(int(begin),1,1,tzinfo=tz) if begin else None
        stop=datetime.datetime(int(end),12,31,tzinfo=tz) if end else None
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        #wells = ['B37E0275','B37E0312','B37E3473','B37E3502','B37E3507']
        #screens = ['B37E0275/001','B37E0312/004','B37E3473/004','B37E3502/001','B37E3507/001']

        #for w in Well.objects.filter(name__in=wells):
        queryset = [get_object_or_404(Well,pk=pk)] if pk else Well.objects.filter(owner=owner)
        for w in queryset:
            data = chart_for_well(w,start=start,stop=stop)
            filename = os.path.join(folder,slugify(unicode(w)) + '.png')
            print filename
            with open(filename,'wb') as png:
                png.write(data)
            if not noscreen:
                for s in w.screen_set.all():
                    data = chart_for_screen(s,start=start,stop=stop)
                    filename = os.path.join(folder,slugify(unicode(s)) + '.png')
                    print filename
                    with open(filename,'wb') as png:
                        png.write(data)

            