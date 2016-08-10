# -*- coding: utf-8 -*-
'''
Created on Feb 9, 2015

@author: theo
'''

from acacia.data.generators import sws
from acacia.meetnet.models import MonFile, Channel, LoggerDatasource
from acacia.data.models import SourceFile

import datetime, pytz
import re, binascii
from django.core.files.base import ContentFile

def create(source, generator=sws.Diver()):
    
    # default timeone for MON files = CET
    CET = pytz.timezone('CET')
    
    headerdict = generator.get_header(source)
    mon = MonFile()
    header = headerdict['HEADER']
    mon.company = header.get('COMPANY',None)
    mon.compstat = header.get('COMP.STATUS',None)
    if 'DATE' in header and 'TIME' in header:
        dt = header.get('DATE') + ' ' + header.get('TIME')
        mon.date = datetime.datetime.strptime(dt,'%d/%m/%Y %H:%M:%S').replace(tzinfo=CET)
    else:
        mon.date = datetime.datetime.now(CET)
    mon.monfilename = header.get('FILENAME',None)
    mon.createdby = header.get('CREATED BY',None)
    mon.num_points = int(header.get('Number of points','0'))
    
    s = headerdict['Logger settings']
    instype = s.get('Instrument type',None)
    parts = instype.split('=')
    mon.instrument_type = parts[-1] 
    mon.status = s.get('Status',None)
    serial = s.get('Serial number',None)
    if serial is not None:
        serial = re.split(r'[-\s+]',serial)[1]
    mon.serial_number = serial
    mon.instrument_number = s.get('Instrument number',None)
    mon.location = s.get('Location',None)
    mon.sample_period = s.get('Sample period',None)
    mon.sample_method = s.get('Sample method','T')
    mon.num_channels = int(s.get('Number of channels','1'))

    s = headerdict['Series settings']
    mon.start_date = datetime.datetime.strptime(s['Start date / time'],'%S:%M:%H %d/%m/%y').replace(tzinfo=CET)    
    mon.end_date = datetime.datetime.strptime(s['End date / time'], '%S:%M:%H %d/%m/%y').replace(tzinfo=CET)    

    channels = []
    for i in range(mon.num_channels):
        channel = Channel(number = i+1)
        name = 'Channel %d' % (i+1)
        s = headerdict[name]
        channel.identification = s.get('Identification',name)
        t = s.get('Reference level','0 -')
        channel.reference_level, channel.reference_unit = re.split(r'\s+',t)
        channel.range, channel.range_unit = re.split(r'\s+', s.get('Range','0 -'))
        channel.range_unit = repr(channel.range_unit)
        channel.reference_unit = repr(channel.reference_unit)
        channels.append(channel)
    return (mon, channels)

def save(request,f):
    mon, channels = create(f)
    mon.user = request.user

    #find  datasource by logger serial number
    mon.datasource = LoggerDatasource.objects.get(logger__serial__iexact = mon.serial_number)

    try:
        sf = mon.datasource.sourcefiles.get(name=f.name)
    except:
        sf = SourceFile(name=f.name,datasource=mon.datasource,user=request.user)

    f.seek(0)
    contents = f.read()
    sf.crc = abs(binascii.crc32(contents))
    sf.file.save(name = f.name, content=ContentFile(contents))
    sf.save()
    
    mon.save()
    
if __name__ == '__main__':
    with open('/home/theo/acaciadata.com/gorinchem/media/gorinchem/g-pb01/g-pb01001/datafiles/r1786/g-pb01_141103113912_R1786.MON') as f:
        mon = create(f)
        