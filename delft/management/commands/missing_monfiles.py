'''
Created on Dec 6, 2014

@author: theo
'''

from django.core.management.base import BaseCommand
from acacia.meetnet.models import MonFile
from django.conf import settings
import os

class Command(BaseCommand):
    args = ''
    help = 'Print list of missing mon files'

    def find(self, name):
        result = []
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            if name in files:
                result.append(os.path.join(root,name))
        return result
    
    def handle(self, *args, **options):
        count = 0
        for mon in MonFile.objects.all():
            try:
                mon.file.open()
                mon.file.close()
            except:
                count += 1
                print count, mon, mon.file
                result = self.find(str(mon))
                matches = len(result)
                if matches == 1:
                    print '  ==> FOUND: ', result[0]
                elif matches > 1:
                    print '  ==> MATCHES: ', result

        print count, "missing files"