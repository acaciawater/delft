'''
Created on Dec 18, 2017

@author: theo
'''
from acacia.meetnet.views import NetworkView
from acacia.meetnet.models import Network, Well, Screen
from django.http.response import JsonResponse, HttpResponseServerError
from django.views.generic.detail import DetailView
import json
from django.conf import settings
from django.utils.translation import gettext_lazy as _

screen_filters = {
    'filter': 'nr',
    'aquifer': 'aquifer__icontains',
}

well_filters = {
    'straat': 'straat__icontains',
    'plaats': 'plaats__icontains',
    'postcode': 'postcode__icontains',
    'name': 'name__icontains',
    'nitg': 'nitg__icontains',
}

def filter_wells(request):    
    from django.db.models import Q
    query = Well.objects.all()
    term = request.GET.get('search')
    if term:
        query = query.filter(
            Q(straat__icontains=term)|
            Q(postcode__icontains=term)|
            Q(plaats__icontains=term)|
            Q(name__icontains=term)|
            Q(nitg__icontains=term))
    aquifer = request.GET.get('aquifer')
    if aquifer and aquifer != 'all':
        ids = Screen.objects.filter(aquifer__iexact=aquifer).values_list('well__id')
        query = query.filter(id__in=ids)
    return query

class HomeView(NetworkView):
    template_name = 'delft/home.html'

    def get_context_data(self, **kwargs):
        context = NetworkView.get_context_data(self, **kwargs)
        options = {
            'center': [52.15478, 4.48565],
            'zoom': 12 }
        
        context['api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['options'] = json.dumps(options)
        context['search'] = self.request.GET.get('search')
        context['wells'] = filter_wells(self.request)

        # get distinct, case insensitive, sorted list of aquifers
        #context['aquifers'] = Screen.objects.distinct('aquifer') # postgres only
        aquifers = set(map(lambda x:str(x[0]).lower(),Screen.objects.exclude(aquifer__isnull=True).values_list('aquifer')))
        aquifers.remove('')

        # get selected aquifer
        aquifer = self.request.GET.get('aquifer')
        if aquifer == _('all'):
            aquifer = None
        context['aquifer'] = aquifer  

        if aquifer:
            # remove selected aquifer from the list
            aquifers.remove(aquifer)

        context['aquifers'] = [_('all')] + sorted(aquifers)
        return context

    def get_object(self):
        return Network.objects.first()

class PopupView(DetailView):
    """ returns html response for leaflet popup """
    model = Well
    template_name = 'meetnet/well_info.html'

def well_locations(request):
    """ return json response with well locations
    """
    result = []
    for p in filter_wells(request):
        try:
            pnt = p.latlon()
            result.append({'id': p.id, 'name': p.name, 'nitg': p.nitg, 'description': p.description, 'lon': pnt.x, 'lat': pnt.y})
        except Exception as e:
            return HttpResponseServerError(unicode(e))
    return JsonResponse(result,safe=False)
