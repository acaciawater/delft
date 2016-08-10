'''
Created on Dec 5, 2014

@author: theo
'''

'''
Created on Feb 13, 2014

@author: theo
'''
from optparse import make_option
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Network
from acacia.data.models import Project, ProjectLocatie, MeetLocatie, Generator
from django.contrib.auth.models import User

class Command(BaseCommand):
    args = ''
    help = 'Maak acaciadata.com projectstructuur'
    option_list = BaseCommand.option_list + (
            make_option('--netwerk',
                action='store',
                type = 'string',
                dest = 'netwerk',
                default = 'Delft'),
        )

    def handle(self, *args, **options):
        
        netwerk = Network.objects.get(name=options.get('netwerk'))
        generator = Generator.objects.get(name='Schlumberger')
        user = User.objects.get(username='theo')

        # create project
        project, created = Project.objects.get_or_create(name = netwerk.name)
        for w in netwerk.well_set.all():
            # create projectlocatie
            ploc, created = ProjectLocatie.objects.get_or_create(project=project, name = w.name, defaults = {'location': w.location })
            for s in w.screen_set.all():
                # create meetlocatie
                mloc, created = MeetLocatie.objects.get_or_create(projectlocatie=ploc, name=unicode(s), defaults = {'location': w.location})
#                 #create datasources
#                 for d in s.datalogger_set.all():
#                     ds, created = LoggerDatasource.objects.get_or_create(logger=d, meetlocatie=mloc, name=d.serial, defaults = { 'generator':generator, 'user': user} )
