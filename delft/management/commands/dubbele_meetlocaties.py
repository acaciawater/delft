'''
Created on Dec 6, 2014

@author: theo
'''

from django.core.management.base import BaseCommand
from acacia.data.models import MeetLocatie, ProjectLocatie
from django.db.models.aggregates import Count

class Command(BaseCommand):
    args = ''
    help = 'Print list of duplicate meetlocaties per projectlocatie'

    def handle(self, *args, **options):
        count = 0
        for pl in ProjectLocatie.objects.all():
            ml = pl.meetlocatie_set.all()
            if ml.count() > 1:
                print '\n'.join(map(str,list(ml)))
                count += 1
        print count, "duplicates"