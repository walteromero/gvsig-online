# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
@author: José Badía <jbadia@scolab.es>
'''
from django.db import models
from gvsigol import settings
from gvsigol_services.models import Datastore
from django.utils.translation import ugettext as _



class Provider(models.Model):   
    type = models.CharField(max_length=100)
    category = models.CharField(max_length=100, null=True, blank=True)
    
    #datastore = models.ForeignKey(Datastore, null=True, blank=True)
    #resource = models.CharField(max_length=100, null=True, blank=True)   
    params = models.TextField()
    
    #table_name = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    image = models.ImageField(upload_to='images', default=settings.STATIC_URL + 'img/geocoding/toponimo.png', null=True, blank=True)
    order = models.IntegerField(null=False, default=10)
    last_update = models.DateTimeField(auto_now_add=False, null=True, blank=True) 
    
    def __unicode__(self):
        return  self.type + '-' + self.pk