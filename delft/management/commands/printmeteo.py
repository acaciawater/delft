'''
Created on Dec 6, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Well
from acacia.data.knmi.models import Station
from .meteo import sort_objects

class Command(BaseCommand):
    args = ''
    help = 'Meteostations printen per put'
                        
    def handle(self, *args, **options):
        for w in Well.objects.all():
            closest = sort_objects(Station.objects.all(), w.location)
            print w.id, w.name, ','.join(c.naam for c in closest[:3])