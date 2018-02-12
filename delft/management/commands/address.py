'''
Created on Sep 5, 2017

@author: theo
'''
from django.core.management.base import BaseCommand
import logging
 
from acacia.meetnet.models import Well
from acacia.data.util import get_address
from acacia.meetnet.util import set_well_address

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Adres gegevens ophalen bij Google'
    
    def add_arguments(self, parser):
        parser.add_argument('-w','--well',
                action='store',
                type=int,
                dest='pk')

    def handle(self, *args, **options):
        pk = options.get('pk',None)
        if pk:
            query = Well.objects.filter(pk=pk)
        else:
            query = Well.objects.all()
        for well in query:
            logger.info('Checking well {}'.format(well))
            if well.straat:
                # already has address
                continue
            if set_well_address(well):
                well.save()

