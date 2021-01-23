'''
Created on Jan 20, 2021

@author: theo
'''
from django.contrib.auth.models import User
from django.test import TestCase

from acacia.data.models import Series
from models import Alarm, Inspector, Receiver
import numpy as np
import pandas as pd


class TestAlarm(TestCase):

    def setUp(self):
        self.user, _ = User.objects.get_or_create(username='test')
        
        index = pd.date_range('2020-01-01', periods=24, freq='H')  
        values = 24 * [0]

        self.series, _ = Series.objects.get_or_create(name='zeros', user=self.user, timezone='UTC')
        self.series.replace_data(pd.Series(index=index, data=values))
        
        Inspector.objects.get_or_create(name='change', classname='delft.models.Changed')
        Inspector.objects.get_or_create(name='offline', classname='delft.models.Offline')
        Inspector.objects.get_or_create(name='online', classname='delft.models.Online')
        
        Receiver.objects.get_or_create(name='Theo', email='tkleinen@gmail.com')

    def tearDown(self):
        pass

    def testChanged(self):
        data = self.series.to_pandas()
        data.iloc[11] = 1.0
        changed, _ = Series.objects.get_or_create(name='changed', user=self.user, timezone='UTC')
        changed.replace_data(data, clear_all=True)
        alarm, _ = Alarm.objects.get_or_create(series=changed,
                             inspector=Inspector.objects.get(name='change'),
                             options='{"tolerance": 0.05}')
        events = alarm.inspect()
        self.assertEqual(len(events), 2)
        
    def testDied(self):
        data = self.series.to_pandas()
        died, _ = Series.objects.get_or_create(name='died', user=self.user, timezone='UTC')
        died.replace_data(data, clear_all=True)
        alarm, _ = Alarm.objects.get_or_create(series=died,
                             inspector=Inspector.objects.get(name='offline'),
                             options='{"start": "2020-01-01 01:00", "stop": "2020-02-01 00:00"}')
        events = alarm.inspect()
        self.assertEqual(len(events), 1)

    def testRevived(self):
        data = self.series.to_pandas()
        data[data.index < "2020-01-01 12:00:00"] = np.nan
        data.dropna(inplace=True)
        alive, _ = Series.objects.get_or_create(name='revived', user=self.user, timezone='UTC')
        alive.replace_data(data, clear_all=True)
        alarm, _ = Alarm.objects.get_or_create(series=alive,
                             inspector=Inspector.objects.get(name='online'),
                             options='{"start": "2020-01-01 01:00", "stop": "2020-01-02 01:00"}')
        events = alarm.inspect()
        self.assertEqual(len(events), 1)
        
