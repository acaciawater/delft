'''
Created on Sep 5, 2017

@author: theo
'''
from django.core.management.base import BaseCommand
import logging
 
from acacia.meetnet.models import Well
from acacia.data.util import toWGS84
from django.conf import settings 

import requests

logger = logging.getLogger(__name__)

def get_address(lon, lat):        
    ''' haal adres gegevens op met google maps geocoding api '''
    url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={key}'.format(lon=lon,lat=lat,key=settings.GOOGLE_MAPS_API_KEY)
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json()

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
                continue
            loc = well.latlon()
            data = get_address(loc.x, loc.y)
            for address in data['results']:
                logger.info(address.get('formatted_address','Geen adres'))
                # first result is closest address
                found = False
                for comp in address['address_components']:
                    types = comp['types']
                    value = comp['long_name']
                    if 'street_number' in types:
                        well.huisnummer = value
                        found = True
                    elif 'route' in types:
                        well.straat = value
                        found = True
                    elif 'locality' in types:
                        well.plaats = value
                        found = True
                    elif 'postal_code' in types:
                        well.postcode = value
                        found = True
                if found:
                    well.save()
                    break

