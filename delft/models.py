from datetime import datetime
import json

from django.core.mail.message import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from acacia.data.models import Series, classForName
import pandas as pd
from django.urls.base import reverse
from acacia.meetnet.models import Well
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone


class Inspector(models.Model):
    ''' 
    Inspector plugin
    wrapper for inspectors that generate events for time series 
    '''
    name = models.CharField(max_length=50, verbose_name=_('naam'), unique=True)
    classname = models.CharField(max_length=50, verbose_name=_('python klasse'),
                                 help_text=_('volledige naam van de inspector klasse, bijvoorbeeld delft.models.Changed'))
    description = models.TextField(blank=True, null=True, verbose_name=_('omschrijving'))
    options = models.TextField(null=True, blank=True, verbose_name=_('default options'))
    
    def get_class(self):
        return classForName(self.classname)
    
    def get_options(self, **kwargs):
        ''' return options, combined with supplied keyword arguments '''
        options = json.loads(self.options or '{}')
        options.update(**kwargs)
        return options
    
    def inspect(self, alarm, data, **kwargs):
        ''' run the inspector plugin '''
        inspector = self.get_class()(alarm)
        options = self.get_options(**kwargs)
        return inspector.inspect(data, **options)
    
    def __str__(self):
        return self.name
        
    class Meta:
        ordering = ['name', ]


class InspectorBase:
    ''' Base class for inspectors '''

    def __init__(self, alarm):
        self.alarm = alarm
        
    def check(self, data, **options):
        ''' check data 
        parameters:
          data: pandas time series
          options: 
            arguments to pass to check method
          returns:
            boolean pandas time series 
        '''
        raise NotImplementedError

    def check_not(self, data, **options):
        ''' invert check results '''
        return ~self.check(data, **options)
    
    def message(self, time, value, result):
        ''' message text for an event
        parameters:
          time: time of event
          value: offending value
          result: result of check
        '''
        return 'Event occurred at time={:%c}, value={}, result={}'.format(time, value, result)
            
    def inspect(self, data, invert=False, **options):
        ''' inspect the data and return events
        parameters:
          data: pandas time series
          invert: when true, run inverse checks
          options: options to pass to check method of inspector
        returns:
          list of events 
        ''' 
        if data.empty:
            return []

        checked = self.check_not(data, **options) if invert else self.check(data, **options)
        checked = checked.dropna()  
        data = data.reindex(checked.index)
        df = pd.DataFrame({'data': data, 'result': checked})
        return [Event(alarm=self.alarm,
                      time=time,
                      message=self.message(time, value, result))
                  for time, value, result in df.itertuples(index=True)
                ]

    
class Changed(InspectorBase):
    ''' inspector that checks for value changes '''

    def check(self, data, **options):
        ''' 
        check for value changes
        options:
          tolerance: maximum change between two consecutive values
        '''
        tol = options.get('tolerance', 0.02)
        diff = data.diff()
        return diff.where(diff.abs() > tol)
    
    def message(self, time, value, result):
        return 'Verandering van {change:+.2f} geconstateerd, waarde={value:.2f}'.format(change=result, time=time, value=value)


def tz_same(t1, t2, tz='utc'):
    ''' make sure t1 and t2 have same timezone
    parameters:
      t1, t2: datetime or pd.Timestamp
      tz: default timezone
    returns:
      t1,t2 with same timezone 
    '''
    if not t1.tzinfo:
        t1 = t1.tz_localize(t2.tzinfo or tz)
    if not t2.tzinfo:
        t2 = t2.tz_localize(t1.tzinfo or tz)
    t1 = t1.tz_convert(t2.tzinfo)
    return  t1, t2

    
class NoData(InspectorBase):
    ''' inspector that checks for nodata '''

    def check(self, data, **options):
        ''' 
        check for nodata
        options:
          freq: check frequency
          start: first time to check
          stop: last time to check
        '''
        freq = options.get('freq', 'H')
        counts = data.resample(freq).count()
        if 'start' in options or 'stop' in options:
            # start and stop should have same timezone
            start, stop = tz_same(pd.Timestamp(options.get('start') or counts.index.min()),
                                  pd.Timestamp(options.get('stop') or counts.index.max()))
            # use Timestamp.ceil() to round time stamps to desired frequency
            index = pd.date_range(start.ceil(freq), stop.ceil(freq), freq=freq)
            counts = counts.reindex(index, fill_value=0)
        return counts.where(counts == 0)
    
    def message(self, time, value, result):
        return 'Geen gegevens'


class Offline(NoData):
    ''' inspector that checks if there was an interruption in the data '''
     
    def check(self, data, **options):
        ''' 
        check for interruptions (offline)
        options:
          freq: resample frequency
          start, stop: time range to check
          size: size of window (number of consecutive nodata values) 
        '''
        nodata = NoData.check(self, data, **options)
        size = options.get('size', 6)
        counts = nodata.rolling(size).count()
        targets = counts.where(counts == size)
        diff = counts.diff()
        return targets.where(diff == 1)


class Online(NoData):
    ''' inspector that checks if data is online again (after offline period) '''

    def check(self, data, **options):
        ''' 
        check if online (there is data after more than 5 consecutive nodata values)
        options:
          freq: resample frequency
          start, stop: time range to check
          size: size of window (number of consecutive nodata values)
        '''
        nodata = NoData.check(self, data, **options)
        size = options.get('size', 6)
        counts = nodata.rolling(size).count()
        targets = counts.where(counts == size - 1)
        diff = counts.diff()
        return targets.where(diff == -1)

    def message(self, time, value, result):
        return 'Er zijn weer gegevens: waarde={:.2f}'.format(value)


class Recipient(models.Model):
    ''' Recipient receives emails about events '''
    name = models.CharField(max_length=100)
    email = models.EmailField()
    salutation = models.CharField(max_length=100, default='Dear')
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    
class Alarm(models.Model):
    ''' Handles alarms for time series '''
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    inspector = models.ForeignKey(Inspector, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(Recipient)
    options = models.TextField(null=True, blank=True, verbose_name=_('options'))
    active = models.BooleanField(default=True)

    # email stuff    
    subject = models.CharField(max_length=200, verbose_name=_('subject'), default=_('subject'))
    message_text = models.TextField(null=True, blank=True, verbose_name=_('Message'))         

    def get_options(self, **kwargs):
        ''' return options dict, combined with supplied keyword arguments '''
        options = json.loads(self.options or '{}')
        options.update(**kwargs)
        return options
    
    def _create_email(self, recipient, **options):
        ''' 
        create email to send to the recipient
        '''
        email = EmailMultiAlternatives(subject=self.subject, to=(recipient.email,))
        context = {
            'name': recipient.name,
            'salutation': recipient.salutation,
            'text': self.message_text,
            'series': self.series,
            }
        context.update(**options)
        email.body = render_to_string('delft/notify_email_nl.txt', context)
        email.html = render_to_string('delft/notify_email_nl.html', context)
        email.attach_alternative(email.html, 'text/html')
        return email
    
    def create_emails(self, events):
        ''' 
        create emails to send to all registered recipients
        returns generator with created emails
        '''
        options = {'events': events}

        try:
            # try to find well-detail url for this series
            well = Well.objects.get(name=self.series.projectlocatie().name)
            site = get_current_site(request=None)
            options.update(detail = 'http://' + site.domain + reverse('meetnet:well-detail',args=(well.id,)))
        except Exception as e:
            pass

        for recipient in self.recipients.filter(active=True):
            yield self._create_email(recipient,**options)

        
    def notify(self, events):
        ''' notify recipients about events '''
        recipients = self.recipients.all()
        for email in self.create_emails(events):
#             email.send()
            kwargs = {
                    'subject': email.subject,
                    'text': email.body,
                    'html': email.html,
                    'sent': timezone.now(),
                }
            for e in events:
                message = Message.objects.create(
                    event = e,
                    **kwargs
                    )
                message.recipients.add(*recipients)
                

    def save_events(self, events):
        ''' 
        save events to database
        returns:
          new events 
        '''
        for e in events: 
            event, created = self.event_set.update_or_create(time=e.time, defaults={'message':e.message}) 
            if created:
                yield event


    def inspect(self, notify=True, **kwargs):
        ''' 
        inspect series data, notify recipients and save events
        returns:
          new events 
        '''
        options = self.get_options(**kwargs)
        data = self.series.to_pandas(raw=True, **options)
        events = self.inspector.inspect(self, data, **options)
        if events:
            events = list(self.save_events(events))
            if events and notify:
                # notify recipients (new events only)
                self.notify(events)
        return events
    
    def __str__(self):
        return '{} ({})'.format(self.series, self.inspector)

    
class Event(models.Model):
    ''' time series event '''
    alarm = models.ForeignKey(Alarm)
    time = models.DateTimeField()
    message = models.TextField(null=True, blank=True)
    
    def notify(self):
        ''' notify registered recipients about this event '''
        self.alarm.notify([self])
        
    def __str__(self):
        return str(self.alarm)

class Message(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='messages')
    recipients = models.ManyToManyField(Recipient, related_name='messages')
    subject = models.CharField(max_length=100)
    text = models.TextField()
    html = models.TextField(null=True, blank=True)
    sent = models.DateTimeField(null=True)
    
