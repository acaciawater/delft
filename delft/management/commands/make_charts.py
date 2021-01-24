'''
Created on Apr 13, 2017

@author: theo
'''
from django.core.management.base import BaseCommand
import logging
from acacia.meetnet.actions import make_wellcharts
from acacia.meetnet.models import Well

logger = logging.getLogger(__name__) 

class Command(BaseCommand):
    args = ''
    help = 'Updates well charts'
    
    def add_arguments(self, parser):
        parser.add_argument('--pk',
                action='store',
                type = int,
                dest = 'pk',
                default = None,
                help = 'update chart of single well')

    def handle(self, *args, **options):
        logger.debug('Updating well charts')
        wells = Well.objects.all()
        pk = options.get('pk', None)
        if pk:
            wells = wells.filter(pk=pk)
        make_wellcharts(None,None,wells)
        logger.debug('Done updating well charts')
        