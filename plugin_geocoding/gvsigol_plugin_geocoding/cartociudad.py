# -*- coding: utf-8 -*-
'''
    gvSIG Online.
    Copyright (C) 2007-2015 gvSIG Association.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
'''
@author: Jose Badia <jbadia@scolab.es>
'''
from geopy.compat import urlencode
from geopy.util import logger
import settings
import urllib2
import json, requests

class Cartociudad():
    
    def __init__(self, provider):
        self.urls = settings.GEOCODING_PROVIDER['cartociudad']
        self.providers=[]
        self.append(provider)
        
        
    def get_type(self):
        return 'cartociudad'
        
        
    def append(self, provider):
        self.providers.append(provider)
        
    
    def geocode(self, query, exactly_one):
        '''
        http://localhost:8090/geocodersolr/api/geocoder/candidatesJsonp?q=casas&autocancel=true&limit=20&countrycodes=es
        '''
        params = {
            'q': query,
            'autocancel': self.urls['autocancel'],
            'limit': self.urls['max_results'],
            'countrycodes':self.urls['country_codes'],
            'priority': json.dumps(self.get_provider_priority())
        }

        #url = "?".join((self.urls['candidates_url'], urlencode(params)))
        return self.get_json_from_url(self.urls['candidates_url'], params)
    
    
    def find(self, address_str, exactly_one):
        '''
        http://localhost:8090/geocodersolr/api/geocoder/candidatesJsonp?q=casas&autocancel=true&limit=20&countrycodes=es
        '''
        
        address = json.loads(address_str)
        if address['address[source]'] == 'user':
            params = {
                'id': address['address[id]'],
                'address': address['address[address]'],
                'source': address['address[source]'],
                'type': address['address[type]'],
                'lat': address['address[lat]'],
                'lng': address['address[lng]']
            }
            return params
        
        params = {
            'id': address['address[id]'],
            #'address': address['address[address]'],
            'source': address['address[source]'],
            'type': address['address[type]'],
            'tip_via': address['address[tip_via]'],
            'portal': address['address[portalNumber]']
        }

        #url = "?".join((self.urls['candidates_url'], urlencode(params)))
        return self.get_json_from_url(self.urls['find_url'], params)
        
        

    def reverse(self, coordinate, exactly_one, language): 
        '''
        http://localhost:8090/geocodersolr/api/geocoder/candidatesJsonp?q=casas&autocancel=true&limit=20&countrycodes=es
        '''
        params = {
            'lat': coordinate[1],
            'lon': coordinate[0]
        }
        return self.get_json_from_url(self.urls['reverse_url'], params)
    
    
    @staticmethod   
    def get_json_from_url(url, params):
        response = requests.get(url=url, params=params)
        if response.status_code == 200:
            respuesta = response.content
            if respuesta.startswith('callback('):
                respuesta = respuesta['callback('.__len__():-1]
    
            data = json.loads(respuesta)
            if data:
                return data
        return []
    
    
    def get_provider_priority(self):
        num_total = self.providers.__len__()
        providers_order = {}
        if num_total != 0:
            step = 1/float(num_total)
            for provider in self.providers:
                table_name = provider.type+'-'+str(provider.pk)
                order = provider.order
                if(order == 0 or order >= num_total):
                    order = num_total-1
                providers_order[table_name] = ((num_total-order)*step)
        return providers_order
        