'''
Created on Feb 21, 2015

@author: theo
'''
from acacia.meetnet.views import NetworkView
from acacia.meetnet.models import Network
 
class HomeView(NetworkView):
    def get_object(self):
        return Network.objects.get(name = 'Delft')
    