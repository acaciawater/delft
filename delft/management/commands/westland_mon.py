'''
Created on Feb 13, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
import os
from acacia.meetnet.models import Network
from acacia.meetnet.util import handle_uploaded_files
from django.contrib.auth.models import User
from csv import DictReader
import logging
logger = logging.getLogger(__name__)

class UserProxy(object):
    def __init__(self,username):
        self.user = User.objects.get(username=username)

class Command(BaseCommand):
    args = ''
    help = 'Test mon bestanden naamgeving voor westland'
    proxy = UserProxy('theo')
    network = Network.objects.first()
    
    def add_arguments(self, parser):
        parser.add_argument('-f','--file',
                action='store',
                dest = 'fname',
                default = None,
                help='MON zipfile'
        )
        parser.add_argument('-d','--dir',
                action='store',
                dest = 'dname',
                default = None,
                help='MON zipfile directory'
        )
        parser.add_argument('-l','--lookup',
                action='store',
                dest = 'lookup',
                default = None,
                help='lookup file (csv)'
        )

    def process(self,pathname,lookup):
        logger.info('processing '+ pathname)
        handle_uploaded_files(
            self.proxy,
            self.network,
            [pathname],
            lookup)
                
    def handle(self, *args, **options):
        
        lookup = options.get('lookup')
        if lookup:
            logger.info('Loading lookup file {}'.format(lookup))
            with open(lookup) as f:
                reader = DictReader(f)
                lookup = {
                    row['bestandsnaam']: '{} ({})'.format(row['peilbuisnummer'],row['nummer_locatie'])
                    for row in reader
                }
            logger.info('Lookup file loaded: {} entries'.format(len(lookup)))
                    
        dname = options.get('dname')
        if dname:
            for path,dirs,files in os.walk(dname):
                for fname in files:
                    if fname.lower().endswith('.zip'):
                        self.process(os.path.join(path,fname),lookup)

        fname = options.get('fname')
        if fname.lower().endswith('.zip'):
            self.process(fname,lookup)
