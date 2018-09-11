'''
Created on Apr 11, 2018

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.meetnet.models import LoggerPos

class Command(BaseCommand):
    help = 'Exporteer csv bestand met datalogger installaties'

    def add_arguments(self, parser):
        parser.add_argument('-f','--file',
                action='store',
                dest = 'fname',
                default = 'loggerpos.csv',
                help='CSV file'
        )

    def handle(self, *args, **options):
        fname = options.get('fname')
        with open(fname,'w') as f:
            f.write('logger,filter,start,eind,ophangpunt,kabellengte\n')
            for pos in LoggerPos.objects.order_by('screen','start_date'):
                f.write('{},{},{},{},{},{}\n'.format(pos.logger,pos.screen,pos.start_date.date(),pos.end_date.date(),pos.refpnt,pos.depth))
