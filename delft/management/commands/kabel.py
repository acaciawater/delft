'''
Created on Dec 6, 2014

@author: theo
'''
import csv, datetime
from optparse import make_option
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Well,Screen
import pytz

class Command(BaseCommand):
    args = ''
    help = 'Importeer kabellengtes'
    option_list = BaseCommand.option_list + (
            make_option('--file',
                action='store',
                type = 'string',
                dest = 'fname',
                default = None),
        )
        
    def handle(self, *args, **options):
        fname = options.get('fname')
        CET=pytz.timezone('CET')
        if fname:
            with open(fname,'r') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    NITG = row['nitg']
                    try:
                        well = Well.objects.get(nitg=NITG)
                        filt = int(row['filter'])
                        screen = well.screen_set.get(nr=filt)
                        datumtijd = '%s %s' % (row['datum'], row['tijd'])
                        depth = row.get('kabellengte')
                        if len(depth) > 0:
                            depth = float(depth)
                        else:
                            depth = 0
                        date = datetime.datetime.strptime(datumtijd,'%d-%m-%Y %H:%M')
                        date = date.replace(tzinfo=CET)
                        date = date.date()
                        found = False
                        for lp in screen.loggerpos_set.all():
                            start = lp.start_date.date()
                            if (abs(start - date).days < 2) or (date.year < 2013 and start.year < 2013):
                                found = True
                                print NITG, filt,datumtijd, depth
                                lp.depth = depth
                                lp.save()
                        if not found:
                            print 'NOT FOUND:', NITG, filt,datumtijd, depth
                    except Well.DoesNotExist:
                        print 'Well %s not found' % NITG
                    except Screen.DoesNotExist:
                        print 'Screen %s/%03d not found' % (NITG, filt)
                        