from datetime import datetime
import json

from django.core.mail.message import EmailMultiAlternatives
from django.db import models
from django.db.models.aggregates import Count
from django.template.loader import render_to_string, get_template
from django.utils.translation import ugettext_lazy as _

from acacia.data.models import Series, classForName
import pandas as pd
from django.template.base import Template
from django.template.context import Context


class Inspector(models.Model):
    ''' Inspector plugin
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
    
    def __unicode__(self):
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
        checked = self.check_not(data, **options) if invert else self.check(data, **options)
        checked = checked.dropna()  
        data = data.reindex(checked.index)
        df = pd.DataFrame({'data': data, 'result': checked})
        return [Event(alarm=self.alarm, time=time, message=self.message(time, value, result))
                  for time, value, result in df.itertuples(index=True)]

    
class Changed(InspectorBase):
    ''' inspector that checks for value changes '''

    def check(self, data, **options):
        tol = options.get('tolerance', 0.02)
        diff = data.diff()
        return diff.where(diff.abs() > tol).dropna()
    
    def message(self, time, value, result):
        return 'Verandering van {change:+.2f} geconstateerd op {time:%c}, waarde={value:.2f}'.format(change=result, time=time, value=value)


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
        freq = options.get('freq', 'H')
        counts = data.resample(freq).count()
        if 'start' in options or 'stop' in options:
            # start and stop should have same timezone
            start, stop = tz_same(pd.Timestamp(options.get('start') or data.index.min()),
                                  pd.Timestamp(options.get('stop') or data.index.max()))
            index = pd.date_range(start, stop, freq=freq)
            counts = counts.reindex(index, fill_value=0)
        return counts.where(counts == 0)
    
    def message(self, time, value, result):
        return 'Geen gegevens op tijdstip {:%c}'.format(time)


class Died(NoData):

    def check(self, data, **options):
        ''' died if 6 consecutive nodatas since start '''
        nodata = NoData.check(self, data, **options)
        size = options.get('size', 6)
        counts = nodata.rolling(size).count()
        targets = counts.where(counts == size)
        diff = counts.diff()
        return targets.where(diff == 1)

    def message(self, time, value, result):
        return 'Geen gegevens sinds {:%c}'.format(time)


class Revived(NoData):

    def check(self, data, **options):
        ''' revived if data after more than 5 consecutive nodatas '''
        nodata = NoData.check(self, data, **options)
        size = options.get('size', 6)
        counts = nodata.rolling(size).count()
        targets = counts.where(counts == size - 1)
        diff = counts.diff()
        return targets.where(diff == -1)

    def message(self, time, value, result):
        return 'Weer gegevens sinds {:%c}, (waarde={:.2f})'.format(time, value)


class Receiver(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    salutation = models.CharField(max_length=100,default='Dear')
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    
class Alarm(models.Model):
    ''' Handles alarms for time series '''
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    inspector = models.ForeignKey(Inspector, on_delete=models.CASCADE)
    receivers = models.ManyToManyField(Receiver)
    options = models.TextField(null=True, blank=True, verbose_name=_('options'))
    sent = models.DateTimeField(null=True)
    
    subject = models.CharField(max_length=200, verbose_name=_('subject'), default='Onderwerp')
    text_template = models.TextField(null=True, blank=True, verbose_name=_('Text template'))
    html_template = models.TextField(null=True, blank=True, verbose_name=_('Html template'))
        
    def get_options(self):
        return json.loads(self.options or '{}')

    def create_emails(self, events):
        ''' create emails to send to the registered receivers '''
        text = Template(self.text_template if self.text_template else get_template('delft/notify_email_nl.txt'))
        html = Template(self.html_template if self.html_template else get_template('delft/notify_email_nl.html'))
        for receiver in self.receivers.filter(active=True):
            email = EmailMultiAlternatives(subject=self.subject, to=(receiver.email,))
            context = {'name': receiver.name, 'salutation': receiver.salutation, 'series': self.series, 'events': events}
            email.body = text.render(context)
            email.attach_alternative(html.render(context), 'text/html')
            yield email
    
    def notify(self, events):
        ''' notify receivers about events '''
        for email in self.create_emails(events):
            email.send()
        self.sent = datetime.now()
        self.save(update_fields=('sent',))
                  
    def inspect(self, notify=False):
        options = self.get_options()
        data = self.series.to_pandas(raw=True, **options)
        events = self.inspector.inspect(self, data, **options)
        if events and notify:
            self.notify(events)
        return events
    
    def __unicode__(self):
        return '{}:{}'.format(self.inspector, self.series)

    
class Event(models.Model):
    alarm = models.ForeignKey(Alarm)
    time = models.DateTimeField()
    message = models.TextField(null=True, blank=True)
    
    def notify(self):
        ''' notify registered receivers about this event '''
        self.alarm.notify([self])
        
    def __unicode__(self):
        return str(self.alarm)

    
def check_alarms(notify=False):
    queryset = Series.objects.annotate(alarm_count=Count('alarm')).filter(alarm_count__gt=0)
    for series in queryset:
        for alarm in series.alarm_set:
            alarm.inspect(notify)
            