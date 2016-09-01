'''
Created on Jun 28, 2016

@author: theo
'''
from django.contrib.contenttypes.models import ContentType
import os

from django.core.management.base import BaseCommand
from acacia.data.models import Series, Formula, ManualSeries
from django.utils.text import slugify

class Command(BaseCommand):
    args = ''
    help = 'Fix Content Types for Series and Charts'
        
    def handle(self, *args, **options):
        for model in [Formula, ManualSeries]:
            ct = ContentType.objects.get_for_model(model)
            for f in ManualSeries.objects.all():
                if hasattr(f,'series_ptr_id'): # can use issublasss() here?
                    s = Series.objects.get(pk=f.series_ptr_id)
                else:
                    s = f
                s.polymorphic_ctype_id = ct.id
                s.save()
