'''
Created on Feb 13, 2014

@author: theo
'''
import csv, datetime
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Network
from django.contrib.gis.geos import Point
from acacia.data.util import RDNEW, toWGS84
from acacia.meetnet.util import register_well, register_screen

class Command(BaseCommand):
    args = ''
    help = 'Importeer csv bestand met metadata van westland'
    def add_arguments(self, parser):
        parser.add_argument('-f','--file',
                action='store',
                dest = 'fname',
                default = None,
                help='CSV file with metadata'
        )

    def handle(self, *args, **options):
        net = Network.objects.get(name='Delft')
        fname = options.get('fname')
        if fname:
            with open(fname,'r') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    nummer = row['nummer_locatie'].strip()
                    peilbuis = row['peilbuisnummer'].strip()
                    name = '{} ({})'.format(peilbuis, nummer)
                    location = toWGS84(Point(x=float(row['x_coordinaat']),y=float(row['y_coordinaat']),srid=RDNEW))
                    well, created = net.well_set.update_or_create(
                        name = name, 
                        defaults = {
                            'location': location, 
                            'maaiveld': float(row['maaiveld mNAP']),
                            'description': row['adres'].strip(),
                            'date': datetime.datetime(1970,1,1),
                            'straat': row['adres'].strip(),
                            'plaats': row['plaats'].strip()
                            }
                        )
                    if created:
                        register_well(well)
                    try:
                        depth = float(row['diepte peilbuis (m tov kop)'])
                        refpnt = float(row['kop peilbuis tov mNAP']) 
                        top = depth - 1
                        bottom = depth
                    except:
                        top = bottom = refpnt = None
                    screen, created = well.screen_set.update_or_create(
                        nr=1,
                        defaults = {
                            'refpnt': refpnt, 
                            'top': top,
                            'bottom': bottom,
                            'depth': depth,
                            'aquifer': 1,
                        }
                    )
                    if created:
                        register_screen(screen)
                    print screen

