'''
Created on Feb 13, 2014

@author: theo
'''
import csv, datetime
from optparse import make_option
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Network, Well
from django.contrib.gis.geos import Point

class Command(BaseCommand):
    args = ''
    help = 'Importeer csv bestand met metadata'
    option_list = BaseCommand.option_list + (
            make_option('--file',
                action='store',
                type = 'string',
                dest = 'fname',
                default = None),
        )

    def handle(self, *args, **options):
        net = Network.objects.get(name='Delft')
        fname = options.get('fname')
        if fname:
            Well.objects.all().delete()
            with open(fname,'r') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    well, created = net.well_set.get_or_create(name=row['Mp'], 
                                                               location = Point(x=float(row['X-coor (m)']),y=float(row['Y-coor (m)'])), 
                                maaiveld=float(row['Maaiveld (m.NAP)']),
                                description=row['Locatie'],
                                nitg=row['TNO-code'],
                                date=datetime.datetime(1980,1,1)
                                )
                    screen, created = well.screen_set.get_or_create(nr=int(row['Filter']),
                                                                    refpnt = float(row['Ref.punt (m NAP)']), 
                                                                    top=float(row['BkF (m -Mv)']),
                                                                    bottom=float(row['OkF (m-Mv)']))
                    print screen

    def handle1(self, *args, **options):
        net = Network.objects.get(name='Delft')
        fname = options.get('fname')
        if fname:
            Well.objects.all().delete()
            with open(fname,'r') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    if row['Prov ZH Cluster'] != 'DSM':
                        continue
                    well, created = net.well_set.get_or_create(name=row['Putcode'], location = Point(x=float(row['X']),y=float(row['Y'])), 
                                maaiveld=0, refpnt = 0,
                                date=datetime.datetime.strptime(row['datum'], '%d/%m/%Y'))
                    screen, created = well.screen_set.get_or_create(nr=int(row['fltr']), 
                                           top=0.0,
                                           bottom=-1.0)
                    if created:
                        print screen
