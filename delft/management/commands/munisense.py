# -*- coding: utf-8 -*-
'''
Created on Dec 21, 2017

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.data.generators.munisense import Munisense
import json
from acacia.meetnet.models import Network
from django.contrib.gis.geos.point import Point

import logging
from acacia.meetnet.util import register_well, register_screen
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    args = ''
    help = 'Importeer wareco putten uit munisense database'

    def add_arguments(self, parser):
        parser.add_argument('-d', '--download',
                action='store_true',
                dest = 'down',
                default = False,
                help = 'download and import')
        parser.add_argument('-x', '--no_import',
                action='store_false',
                dest = 'import',
                default = True,
                help = 'no import into database')
        parser.add_argument('-f', '--filename',
                action='store',
                dest = 'fname',
                default = 'munisense.json',
                help = 'import from file')

    def process(self, network, wells):
        n = 0
        for key,value in wells.items():
            n += 1

            def as_array(key):
                try:
                    return [(int(t),float(x)) for t,x in value[key].items()]
                except:
                    return None

            def as_float(key):
                try:
                    return float(value[key])
                except:
                    return None
                
            object_id = value['object_id']    
            description = value['description']
            
            logger.info('{}: {}'.format(key,description))

            lat = as_float("location_latitude")
            lon = as_float("location_longitude")
            location = value['location_description']
            dino = value["dino_id"]
            bro = value["bro_id"]
            owner = value["owner_id"]
            maaiveld = as_array('well_covering_surface_level')
            last_mv = maaiveld[-1][1] if maaiveld else None
            well,created = network.well_set.update_or_create(name=description or object_id, defaults = {
                'description': u'Munisense ID={}, {}'.format(object_id or description,location),
                'location': Point(lon,lat),
                'nitg': dino,
                'bro': bro,
                'owner': owner,
                'maaiveld': last_mv
                })
            if created:
                logger.info('Well {} created'.format(object_id))
                register_well(well)

            aquifer = value["well_properties_aquifer"]
            depth = as_array("well_properties_depth")
            last_depth = depth[-1][1] if depth else None
            diameter = value["well_properties_diameter"]
            bkb = as_array("well_properties_well_head")
            last_bkb = bkb[-1][1] if bkb else None
            bkf = as_float('well_properties_filter_upper')
            okf = as_float("well_properties_filter_lower")
            screen, created = well.screen_set.update_or_create(nr=1,defaults = {
                'aquifer': aquifer,
                'top': bkf,
                'bottom': okf,
                'refpnt': last_bkb,
                'diameter': diameter,
                'depth': last_depth,
                })
            if created:
                logger.info('Screen {} created'.format(screen))
                register_screen(screen)
        return n
        
    def handle(self, *args, **options):
        importing = options['import']
        down = options['down']
        filename = options['fname']
        network = Network.objects.first()
        numwells = 0
        if down:
            m = Munisense()
            options = {
                'url':'https://wareco-water2.munisense.net/webservices/v2',
                'username': 'ohoes',
                'password': 'Acacia',
            }
            with open(filename,'w') as f:
                chunk = 0
                for response in m.download_wells(**options):
                    contents = response.text
                    if chunk:
                        f.write(',')
                    else:
                        f.write('{')
                    f.write(contents[1:-1])
                    chunk += 1
                    if importing:
                        wells = response.json()
                        numwells += self.process(network,wells)
                if chunk:
                    f.write('}\n')
        else:
            import io
            with io.open(filename) as fp:
                wells = json.load(fp)
                numwells += self.process(network,wells)
        
        print numwells, 'wells processed'
        