'''
Created on Dec 6, 2014

@author: theo
'''
import os, re, binascii, zipfile
from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from acacia.meetnet.models import Well, Screen, Datalogger, LoggerDatasource, LoggerPos
from acacia.data.models import SourceFile, Generator, MeetLocatie
from django.contrib.auth.models import User

import monfile, StringIO

class Command(BaseCommand):
    args = ''
    help = 'Importeer mon files'
    option_list = BaseCommand.option_list + (
            make_option('--dir',
                action='store',
                type = 'string',
                dest = 'dir'),
            make_option('--zip',
                action='store',
                type = 'string',
                dest = 'zip'),
        )

    def process_zip(self,zip):
        print 'Processing', zip
        user = User.objects.get(username='theo')
        generator = Generator.objects.get(name='Schlumberger')
        with zipfile.ZipFile(zip,'r') as z:
            count = 0
            for info in z.infolist():
                if info.filename.endswith('.MON'):
                    name = re.split(r'[_\.\/]',info.filename)
                    if name[-1].startswith('MON'):
                        print 'File', info.filename
                        try:
                            put, filter = name[0].split('-')
                        except:
                            continue
                        try:
                            try:
                                well = Well.objects.get(nitg=put)
                            except Well.DoesNotExist:
                                well = Well.objects.get(name=put)
                            screen = well.screen_set.get(nr=int(filter))
                            try:
                                loc = MeetLocatie.objects.get(name=unicode(screen))
                            except:
                                loc = MeetLocatie.objects.get(name='%s/%s' % (put,filter))
                                
                            with z.open(info.filename, 'r') as f:
                                contents = f.read() 
                                io = StringIO.StringIO(contents)
                                mon, channels = monfile.create(io)
                                serial = mon.serial_number
                                logger, created = Datalogger.objects.get_or_create(serial=serial,defaults={'model': mon.instrument_type})
                                
                                result = logger.loggerpos_set.filter(screen=screen,start_date=mon.start_date,end_date=mon.end_date,refpnt=screen.refpnt)
                                if result:
                                    pos = result[0]
                                else:
                                    pos, created = logger.loggerpos_set.get_or_create(screen=screen,start_date=mon.start_date,end_date=mon.end_date,refpnt=screen.refpnt)
                                
                                # get/create datasource for logger
                                ds, created = LoggerDatasource.objects.get_or_create(name=logger.serial,meetlocatie=loc,
                                                                                     defaults = {'logger': logger, 'generator': generator, 'user': user, 'timezone': 'CET'})
                                
                                mon.crc = abs(binascii.crc32(contents))
                                try:
                                    sf = ds.sourcefiles.get(crc=mon.crc)
                                    print 'Mon file already exist: ', sf
                                except SourceFile.DoesNotExist:
                                    # add source file
                                    filename = os.path.basename(info.filename)
                                    mon.name = mon.filename = filename
                                    mon.datasource = ds
                                    mon.user = ds.user
                                    contentfile = ContentFile(contents)
                                    mon.file.save(name=filename, content=contentfile)
                                    mon.get_dimensions()
                                    mon.save()
                                    mon.channel_set.add(*channels)
                                    pos.monfile_set.add(mon)

                                    print screen, serial, mon.num_points, mon.start_date, mon.end_date
                                    count += 1
                        except Well.DoesNotExist:
                            print 'Well not found:', put
                            continue
                        except Screen.DoesNotExist:
                            print 'Screen not found: %s/%s' % (put, filter)
                            continue
                        except Exception as e:
                            print e, put, filter
        return count

    def handle(self, *args, **options):
        count = 0
        d = options.get('dir')
        if d:
            for path,dirs,files in os.walk(d):
                for f in files:
                    if f.endswith('zip'):
                        z = os.path.join(path,f)
                        count += self.process_zip(z)
        z = options.get('zip')
        if z:
            count = self.process_zip(z)
        print count, '.MON bestanden toegevoegd'
