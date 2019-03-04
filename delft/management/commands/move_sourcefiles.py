import os
import shutil

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from acacia.data.upload import sourcefile_upload
from acacia.data.models import SourceFile

class Command(BaseCommand):
    args = ''
    help = 'Move source files to correct media folder'

    def handle(self, *args, **options):
        storage = default_storage
        for sf in SourceFile.objects.all():
            correct = sourcefile_upload(sf, os.path.basename(sf.file.name))
            if sf.file.name != correct:
#                 print (sf.file.name, correct)
                src = storage.path(sf.file.name)
                dst = storage.path(correct)
                print src
                print dst
                destdir = os.path.dirname(dst)
                if not os.path.exists(destdir):
                    os.makedirs(destdir)
                shutil.move(src, dst)
                sf.file.name = correct
                sf.save(update_fields = ['file'])
