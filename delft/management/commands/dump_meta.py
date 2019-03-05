'''
Created on Jul 20, 2017

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Screen

class Command(BaseCommand):
    args = ''
    help = 'maakt metadata dump'
                        
    def handle(self, *args, **options):
        print("put,nitg,maaiveld,lengtegraad,breedtegraad,filternummer,bovenkantbuis,bovenkantfilter,onderkantfilter")            
        for s in Screen.objects.order_by('well','nr'):
            w=s.well
            coords = w.latlon()
            print(','.join(map(str,[w.name,w.nitg,w.maaiveld,coords.x,coords.y,s.nr,s.refpnt,s.top,s.bottom])))
