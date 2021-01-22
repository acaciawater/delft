from django.core.management.base import BaseCommand

from delft.models import check_alarms

class Command(BaseCommand):
    args = ''
    help = 'Controleer op alarm en verstuur emails'
    def add_arguments(self, parser):
        pass
    
    def handle(self, *args, **options):
        check_alarms(notify=True)
