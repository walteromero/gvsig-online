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

from django.shortcuts import render_to_response, RequestContext, redirect, HttpResponse
from geocoder import Geocoder
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_safe,require_POST, require_GET
from gvsigol_plugin_geocoding.models import Provider
from django.utils.translation import ugettext as _
from gvsigol_auth.utils import superuser_required, staff_required
from forms_services import ProviderForm, ProviderUpdateForm
from django.shortcuts import render
from gvsigol_plugin_geocoding import settings as geocoding_setting
from gvsigol import settings
from gvsigol_plugin_geocoding.utils import *
import json
from gvsigol_services.models import Workspace, Datastore


providers_order = []
geocoder = None

@login_required(login_url='/gvsigonline/auth/login_user/')
@staff_required
def provider_list(request):
    ls = []
    
    providers = None
    if request.user.is_superuser:
        providers = Provider.objects.order_by('order')
    
    response = {
        'providers': providers
    }
    return render_to_response('provider_list.html', response, context_instance=RequestContext(request))



@login_required(login_url='/gvsigonline/auth/login_user/')
@superuser_required
def provider_add(request):        
    if request.method == 'POST':
        form = ProviderForm(request.POST, request.FILES)
        try:
            newProvider = Provider()
            
            type = request.POST.get('type')
            newProvider.type = type
            newProvider.category = request.POST.get('category')
            
            params = request.POST.get('params')
            
            if type=='cartociudad' or type=='user':
                workspace = request.POST.get('workspace')
                datastore = request.POST.get('datastore')
                ws = Workspace.objects.get(id=workspace)
                ds = Datastore.objects.filter(workspace=ws, name=datastore).first()
                
                if type=='user':
                    resource = request.POST.get('resource')
                    id_field = request.POST.get('id_field')
                    text_field = request.POST.get('text_field')
                    geom_field = request.POST.get('geom_field')
                
                    params = {
                        'datastore_id': ds.id,
                        'resource': str(resource),
                        'id_field': str(id_field),
                        'text_field': str(text_field),
                        'geom_field': str(geom_field)
                    }
                
                if type=='cartociudad':
                    if not isValidCartociudadDB():
                        msg = _("Error: DataStore has not a valid CartoCiudad schema")
                        # FIXME: the backend should raise more specific exceptions to identify the cause (e.g. layer exists, backend is offline)
                        form.add_error(None, msg)
                        return render(request,'provider_add.html',{'form': form, 'settings': json.dumps(geocoding_setting.GEOCODING_PROVIDER) })
                    params = {
                        'datastore_id': ds.id,
                    } 
                
            newProvider.params = json.dumps(params)
                
        
            newProvider.order = Provider.objects.all().count()+1
            if request.FILES.get('image'):
                newProvider.image = request.FILES.get('image')  
                    
            newProvider.save()  
            
            #set_providers_actives()
            set_providers_to_geocoder()
            
            return redirect('provider_update', provider_id=newProvider.pk)
            
        except Exception as e:
            try:
                msg = e.get_message()
            except:
                msg = _("Error: provider could not be published")
            # FIXME: the backend should raise more specific exceptions to identify the cause (e.g. layer exists, backend is offline)
            form.add_error(None, msg)

    else:
        form = ProviderForm()
        providers = None
        if request.user.is_superuser:
            providers = Provider.objects.all()
            form.fields['workspace'].queryset = Workspace.objects.filter(created_by__exact=request.user.username)
            
    return render(request,'provider_add.html',{'form': form, 'settings': json.dumps(geocoding_setting.GEOCODING_PROVIDER) })


def isValidCartociudadDB():
    return True


@login_required(login_url='/gvsigonline/auth/login_user/')
@require_http_methods(["GET", "POST", "HEAD"])
@staff_required
def provider_update(request, provider_id):
    provider = Provider.objects.get(id=provider_id)
    if provider==None:
        return HttpResponseNotFound(_('Provider not found'))

    if request.method == 'POST':
        #form = ProviderUpdateForm(request.POST)
        return redirect('provider_list')
    else:
        form = ProviderUpdateForm(instance=provider)
        params = json.loads(provider.params)
        form.fields['category'].initial = provider.category
        
        if provider.type == 'user' or provider.type == 'cartociudad':
            datastore_id = params["datastore_id"]
            datastore = Datastore.objects.get(id=datastore_id)
            
            form.fields['workspace'].initial = datastore.workspace.name
            form.fields['datastore'].initial = datastore.name
            if provider.type == 'user':
                form.fields['resource'].initial = params["resource"]
                form.fields['id_field'].initial = params["id_field"]
                form.fields['text_field'].initial = params["text_field"]
                form.fields['geom_field'].initial = params["geom_field"]
            
        form.fields['params'].initial = provider.params
    
    image_url = settings.STATIC_URL + 'img/geocoding/toponimo.png'
    if provider.image:
        image_url = provider.image.url
        # HACK HTTPS
        image_url = image_url.replace("https", "http")
        
    return render(request, 'provider_update.html', {'form': form, 'params': provider.params, 'type': provider.type, 'provider_id': provider_id, 'image_photo_url': image_url})


@login_required(login_url='/gvsigonline/auth/login_user/')
@require_http_methods(["GET", "POST", "HEAD"])
@staff_required
def provider_update_order(request, provider_id, order):
    provider = Provider.objects.get(id=provider_id)
    if provider!=None and request.method == 'POST':
        provider.order = order
        provider.save()
        #set_providers_actives()
        set_providers_to_geocoder()
        
        return HttpResponse(status=200)
        
    return HttpResponse(status=500)
 
@login_required(login_url='/gvsigonline/auth/login_user/')
@staff_required
def provider_delete(request, provider_id):
    try:
        provider = Provider.objects.get(pk=provider_id)
        if delete_XML_config(provider):
            remove_solr_data(provider)
            remove_solr_config(provider)
            reload_solr_config()
        provider.delete()
        #set_providers_actives()
        set_providers_to_geocoder()
        
    except Exception as e:
        return HttpResponse('Error deleting provider: ' + e, status=500)
    
    return redirect('provider_list')


@login_required(login_url='/gvsigonline/auth/login_user/')
@staff_required
def provider_full_import(request, provider_id):
    provider = Provider.objects.get(pk=provider_id)
    has_config = False
    if provider.type == 'cartociudad':
        has_config = create_cartociudad_config(provider)
    else:
        has_config = create_XML_config(provider)
    if has_config:
        add_solr_config(provider)
        reload_solr_config()
    remove_solr_data(provider)
    full_import_solr_data(provider)
    return redirect('provider_list')

@login_required(login_url='/gvsigonline/auth/login_user/')
@staff_required
def provider_import_status(request, provider_id):
    provider = Provider.objects.get(pk=provider_id)
    response = status_solr_import(provider)
    
    return HttpResponse(json.dumps(response, indent=4), content_type='application/json')
    

@login_required(login_url='/gvsigonline/auth/login_user/')
@staff_required
def provider_delta_import(request, provider_id):
    provider = Provider.objects.get(pk=provider_id)
    if create_XML_config(provider):
        add_solr_config(provider)
        reload_solr_config()
    delta_import_solr_data(provider)
    return redirect('provider_list')


def get_conf(request):
    if request.method == 'POST': 
        response = {
            'candidates_url': geocoding_setting.GEOCODING_PROVIDER['cartociudad']['candidates_url'],
            'find_url': geocoding_setting.GEOCODING_PROVIDER['cartociudad']['find_url'],
            'reverse_url': geocoding_setting.GEOCODING_PROVIDER['cartociudad']['reverse_url']
        }       
        return HttpResponse(json.dumps(response, indent=4), content_type='folder/json')           


@login_required(login_url='/gvsigonline/auth/login_user/')
@staff_required    
def upload_shp_cartociudad(request, provider_id):
    provider = Provider.objects.get(pk=provider_id)
    create_cartociudad_config(provider)
    
    '''
    provider = Provider.objects.get(pk=provider_id)
    if request.method == 'GET':
        file = request.GET.get('file')
        file_municipios = request.GET.get('file_municipios')  
        
        unzip_file('/home/jose/Cartografia/Cartociudad_Valencia/lineas_limite.zip', provider)
        unzip_file('/home/jose/Cartografia/Cartociudad_Valencia/CARTOCIUDAD_CALLEJERO_VALENCIA.zip', provider)
        
        export_shp_municipios_to_postgis(provider)

        export_dbf_to_postgis(provider)
        export_shp_to_postgis(provider)

        cartociudad_full_import(provider)
        remove_temp_files(provider)
        
        return HttpResponse('Hola provider:'+ provider_id, status=200)
    '''        
    return HttpResponse('OK ', status=200)

@login_required(login_url='/gvsigonline/auth/login_user/')
@staff_required 
def upload_shp_cartociudad_status(request):
    status = {}
    if request.method == 'GET':
        status = get_cartociudad_status()
            
    return HttpResponse(json.dumps(status, indent=4), content_type='application/json')
    
    
def search_candidates(request):
    if request.method == 'GET':
        query = request.GET.get('q')  
        suggestions = get_geocoder().search_candidates(query)
            
        return HttpResponse(json.dumps(suggestions, indent=4), content_type='application/json')
    
def find_candidate(request):
    suggestion = {}
    if request.method == 'POST':
        address = json.dumps(request.POST)
        suggestion = get_geocoder().find_candidate(address)
            
    return HttpResponse(json.dumps(suggestion, indent=4), content_type='application/json')


def get_location_address(request):
    if request.method == 'POST':
        coord = request.POST.get('coord')
        type = request.POST.get('type')
        location = get_geocoder().get_location_address(str(coord), type)
        
        return HttpResponse(json.dumps(location, indent=4), content_type='application/json')


def set_providers_to_geocoder():
    providers = Provider.objects.order_by('order')
    global geocoder
    geocoder = Geocoder()
    for provider in providers:
        geocoder.add_provider(provider)
        
def get_geocoder():
    global geocoder
    if not geocoder:
        set_providers_to_geocoder()
    
    return geocoder

