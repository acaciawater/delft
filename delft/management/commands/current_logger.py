'''
Created on Apr 11, 2018

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Screen

class Command(BaseCommand):
    help = 'overzicht huidige loggers (met leeftijd)'

    def add_arguments(self, parser):
        parser.add_argument('-f','--file',
                action='store',
                dest = 'fname',
                default = 'currentloggers.csv',
                help='CSV file'
        )

    def handle(self, *args, **options):
        fname = options.get('fname')
        with open(fname,'w') as f:
            f.write('filter,logger,start,stop,ophangpunt,kabellengte\n')
            for screen in Screen.objects.all():
                if screen.loggerpos_set.exists(): 
                    current = screen.loggerpos_set.latest('start_date')
                    logger = current.logger
                    first_seen = logger.loggerpos_set.earliest('start_date')
                    f.write('{},{},{},{},{},{}\n'.format(screen, logger, first_seen.start_date.date(),current.end_date.date(), current.refpnt, current.depth))
