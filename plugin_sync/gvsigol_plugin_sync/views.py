'''
    gvSIG Online.
    Copyright (C) 2016 gvSIG Association.

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


# generic python modules
import json
import time, os
import shutil
import tempfile
import io
from io import BytesIO
import logging
import sqlite3

# django libs
from django.http.response import StreamingHttpResponse, FileResponse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponse
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_safe,require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from django.http import JsonResponse

# gvsig online modules
from gvsigol_services.models import Workspace, Datastore, LayerGroup, Layer, LayerReadGroup, LayerWriteGroup, LayerLock,\
    LayerResource
from gvsigol_core import geom

from gvsigol_services.backend_mapservice import backend as mapservice_backend
from gvsigol_services.backend_postgis import Introspect
from gvsigol.settings import MEDIA_ROOT

# external libs
import gdaltools
from spatialiteintrospect import introspect as sq_introspect
from PIL import Image


'''
@author: Cesar Martinez Izquierdo - http://www.scolab.es
'''

DEFAULT_BUFFER_SIZE = 1048576


@require_safe
def get_layerinfo(request):
    """
    For the moment return only writable layers, until we manage read-only layers
    in Geopaparazzi
    
    universallyReadableLayers = Layer.objects.exclude(layerreadgroup__layer__isnull=False)
    if not isinstance(request.user, AnonymousUser) :
        user = request.user
        readWriteLayers = Layer.objects.filter(layerwritegroup__group__usergroupuser__user=user)
        readOnlyLayers = Layer.objects.filter(layerreadgroup__group__usergroupuser__user=user).exclude(layerwritegroup__group__usergroupuser__user=user)
        layerJson = layersToJson(universallyReadableLayers, readOnlyLayers, readWriteLayers)
    else:
        layerJson = layersToJson(universallyReadableLayers)
    """
    if not isinstance(request.user, AnonymousUser) :
        user = request.user
        readWriteLayers = Layer.objects.filter(layerwritegroup__group__usergroupuser__user=user)
        layerJson = layersToJson([], [], readWriteLayers)
    else:
        layerJson = layersToJson([], [], [])
    return HttpResponse(layerJson, content_type='application/json')


@require_GET
def get_layerinfo_by_project(request, project):
    """
    For the moment return only writable layers, until we manage read-only layers
    in Geopaparazzi
    
    universallyReadableLayers = Layer.objects.exclude(layerreadgroup__layer__isnull=False).filter(layer_group__projectlayergroup__project=project)
    if not isinstance(request.user, AnonymousUser) :
        user = request.user
        readWriteLayers = Layer.objects.filter(layerwritegroup__group__usergroupuser__user=user).filter(layer_group__projectlayergroup__project=project)
        readOnlyLayers = Layer.objects.filter(layerreadgroup__group__usergroupuser__user=user).filter(layer_group__projectlayergroup__project=project).exclude(layerwritegroup__group__usergroupuser__user=user)
        layerJson = layersToJson(universallyReadableLayers, readOnlyLayers, readWriteLayers)
    else:
        layerJson = layersToJson(universallyReadableLayers)
    """
    if not isinstance(request.user, AnonymousUser) :
        user = request.user
        readWriteLayers = Layer.objects.filter(layerwritegroup__group__usergroupuser__user=user).filter(layer_group__projectlayergroup__project=project)
        layerJson = layersToJson([], [], readWriteLayers)
    else:
        layerJson = layersToJson([], [], [])
    return HttpResponse(layerJson, content_type='application/json')

    
def fill_layer_attrs(layer, permissions):
    row = {}
    geom_info = mapservice_backend.get_geometry_info(layer)
    srid = geom_info['srs']
    if srid is None:
        srid = 'unknown'
    geom_type = geom_info['geomtype']
    row['name'] = layer.get_qualified_name()
    row['title'] = layer.title
    row['abstract'] = layer.abstract
    row['geomtype'] = geom.toGeopaparazzi(geom_type)
    row['srid'] = srid
    row['permissions'] = permissions
    # last-modified excluded for the moment
    #row['last-modified'] = long(time.time())   #FIXME
    return row

def layersToJson(universallyReadableLayers, readOnlyLayers=[], readWriteLayers=[]):
    result = []
    # the queries get some layers repeated if the user has several groups,
    # so we use a set to keep them unique
    layerIds = set()
    for layer in readWriteLayers:
        if not layer.id in layerIds:
            row = fill_layer_attrs(layer, 'read-write')
            result.append(row)
            layerIds.add(layer.id)
            
    for layer in readOnlyLayers:
        if not layer.id in layerIds:
            row = fill_layer_attrs(layer, 'read-only')
            result.append(row)
            layerIds.add(layer.id)
    
    for layer in universallyReadableLayers:
        if not layer.id in layerIds:
            row = fill_layer_attrs(layer, 'read-only')
            result.append(row)
            layerIds.add(layer.id)
            
    layerStr = json.dumps(result)
    return layerStr 

@login_required(login_url='/gvsigonline/auth/login_user/')
@require_POST
def sync_download(request):
    locks = []
    prepared_tables = []
    try:
        request_params = json.loads(request.body)
        layers = request_params["layers"]
        # we will ignore bbox for the moment
        bbox = request_params.get("bbox", None)
        for layer in layers:
            #FIXME: maybe we need to specify if we want the layer for reading or writing!!!! Assume we always want to write for the moment
            lock = add_layer_lock(layer, request.user)
            locks.append(lock)
            conn = _get_layer_conn(lock.layer)
            if not conn:
                raise HttpResponseBadRequest("Bad request")
            prepared_tables.append({"layer": lock.layer, "connection": conn})
        
        (fd, file_path) = tempfile.mkstemp(suffix=".sqlite", prefix="syncdwld_")
        os.close(fd)
        os.remove(file_path)
        if len(prepared_tables)>0:
            ogr = gdaltools.ogr2ogr()
            ogr.set_output_mode(
                    layer_mode=ogr.MODE_LAYER_CREATE,
                    data_source_mode=ogr.MODE_DS_CREATE_OR_UPDATE)
            for table in prepared_tables:
                ogr.set_input(
                        table["connection"],
                        table_name=table["layer"].name
                ).set_output(
                        file_path,
                        table_name=table["layer"].get_qualified_name()
                ).execute()

            gdaltools.ogrinfo(file_path, sql="SELECT UpdateLayerStatistics()")
            locked_layers = [ lock.layer for lock in locks]
            _copy_images(locked_layers, file_path)
            file = TemporaryFileWrapper(file_path)
            response = FileResponse(file, content_type='application/spatialite')
            #response['Content-Disposition'] = 'attachment; filename=db.sqlite'
            #response['Content-Length'] = os.path.getsize(path)
            return response
        else:
            return HttpResponseBadRequest("Bad request")

    except Exception as exc:
        for layer in locks:
            remove_layer_lock(lock.layer, request.user)
        logging.error("sync_download error")
        return HttpResponseBadRequest("Bad request")

def add_layer_lock(qualified_layer_name, user):
    (ws_name, layer_name) = qualified_layer_name.split(":")
    layer_filter = Layer.objects.filter(name=layer_name, datastore__workspace__name=ws_name)
    #ugu = UserGroupUser.objects.filter(user=user)
    #lwg = LayerWriteGroup.objects.filter(group__usergroupuser__user=user)
    is_writable = (layer_filter.filter(layerwritegroup__group__usergroupuser__user=user).count()>0)
    
    if not is_writable:
        raise PermissionDenied
    layer = layer_filter[0]
    
    #is_locked = (LayerLock.objects.filter(layer__name=layer_name, layer__datastore__workspace__name=ws_name).count()>0)
    is_locked = (LayerLock.objects.filter(layer=layer).count()>0)
    if is_locked:
        raise LayerLocked
    new_lock = LayerLock()
    new_lock.layer = layer
    new_lock.created_by = user.username
    new_lock.save()
    return new_lock

def is_locked(qualified_layer_name, user, check_writable=False):
    (ws_name, layer_name) = qualified_layer_name.split(":")
    layer_filter = Layer.objects.filter(name=layer_name, datastore__workspace__name=ws_name)
    
    if check_writable:
        is_writable = (layer_filter.filter(layerwritegroup__group__usergroupuser__user=user).count()>0)
        if not is_writable:
            raise PermissionDenied
    layer = layer_filter[0]
    return (LayerLock.objects.filter(layer=layer, created_by=user.username).count()>0)

def get_layer_lock(qualified_layer_name, user, check_writable=False):
    name_parts = qualified_layer_name.split(":")
    if len(name_parts)==2:
        # only consider tables having a proper qualified name (e.g., using the schema: workspace:layer_name)
        (ws_name, layer_name) = name_parts
        layer_filter = Layer.objects.filter(name=layer_name, datastore__workspace__name=ws_name)
        
        if check_writable:
            is_writable = (layer_filter.filter(layerwritegroup__group__usergroupuser__user=user).count()>0)
            if not is_writable:
                raise PermissionDenied
        layer = layer_filter[0]
        locks = LayerLock.objects.filter(layer=layer, created_by=user.username)
        if locks.count()>0:
            return locks[0]
        else:
            raise LayerNotLocked(qualified_layer_name)
    return None

def remove_layer_lock(layer, user, check_writable=False):
    layer_lock = LayerLock.objects.filter(layer=layer)
    if len(layer_lock)==1:
        if layer_lock.filter(created_by=user.username).count()!=1:
            # the layer was locked by a different user!!
            raise PermissionDenied()
        if check_writable:
            layer_filter = Layer.objects.filter(id=layer.id)
            is_writable = (layer_filter.filter(layerwritegroup__group__usergroupuser__user=user).count()>0)
            if not is_writable:
                raise PermissionDenied()
        layer_lock.delete()
        return True
    raise LayerNotLocked()


@login_required(login_url='/gvsigonline/auth/login_user/')
@require_POST
def sync_upload(request):
    tmpfile = None

    if 'fileupload' in request.FILES:
        tmpfile = handle_uploaded_file(request.FILES.get('fileupload'))
    elif 'fileupload' in request.POST:
        try:
            zipcontents = request.POST.get('fileupload')
            tmpfile = handle_uploaded_file_base64(zipcontents)
        except:
            #syncLogger.exception("'zipfile' param missing or incorrect")
            return HttpResponseBadRequest("'fileupload' param missing or incorrect")
    elif request.method == 'POST':
        tmpfile = handle_uploaded_file_raw(request)
    else:
        #syncLogger.error("'zipfile' param missing or incorrect")
        return HttpResponseBadRequest("'fileupload' param missing or incorrect")
    if tmpfile:
        # 1 - check if the file is a spatialite database
        # 2 - check if the included tables are locked and writable by the user
        # 3 - overwrite the tables in DB using the uploaded tables
        # 4 - remove the table locks
        # 5 - handle images
        # 6 - remove the temporal file
        try:
            db = sq_introspect.Introspect(tmpfile)
            try:
                tables = db.get_geometry_tables()
                locks = []
                for t in tables:
                    # first check all the layers are properly locked and writable
                    lock = get_layer_lock(t, request.user, check_writable=True)
                    locks.append(lock)
                for lock in locks:
                    ogr = gdaltools.ogr2ogr()
                    geom_info = db.get_geometry_columns_info(t)
                    if len(geom_info)>0 and len(geom_info[0])==7:
                        srs = "EPSG:"+str(geom_info[0][3])
                        ogr.set_input(tmpfile, table_name=t, srs=srs)
                        conn = _get_layer_conn(lock.layer)
                        if not conn:
                            raise HttpResponseBadRequest("Bad request")
                        ogr.set_output(conn, table_name=lock.layer.name)
                        ogr.set_output_mode(ogr.MODE_LAYER_OVERWRITE, ogr.MODE_DS_UPDATE)
                        ogr.execute()
            finally:
                db.close()
            
            import time
            # approach 1
            t1 = time.clock()
            layers = [ lock.layer for lock in locks]
            replacer = ResourceReplacer(tmpfile, layers)
            replacer.process()
            t2 = time.clock()
            
            # approach 2
            _remove_existing_images(layers)
            _extract_images(tmpfile)
            t3 = time.clock()
            
            print "Time approach 1: " + str(t2-t1)
            print "Time approach 2: " + str(t3-t2)
            
            # everything was fine, release the locks now
            for lock in locks:
                lock.delete()
        except sq_introspect.InvalidSqlite3Database:
            return HttpResponseBadRequest("The file is not a valid Sqlite3 db")
        except LayerNotLocked as e:
            return HttpResponseBadRequest("Layer is not locked: {0}".format(e.layer))
        except:
            raise
        finally:
            os.remove(tmpfile)
    return JsonResponse({'response': 'OK'})

def _remove_existing_images(tables):
    resources = LayerResource.objects.filter(layer__name__in=tables, type=LayerResource.EXTERNAL_IMAGE)
    for r in resources:
        img_path = r.path
        if os.path.isfile(img_path):
            os.remove(img_path)
    resources.delete()
    for r in resources:
        # should print nothing as we have removed all the resources
        print r

def _extract_images(db_path):
    """
    Extracts images from the sqlite database to the server side (LayerResource
    table + file system images)
    """
    conn = sqlite3.connect(db_path)    
    try:
        cursor = conn.cursor()
        sql = "SELECT id, restable, rowidfk, resblob, resname FROM geopap_resource WHERE type = 'BLOB_IMAGE'"
        result = cursor.execute(sql)
        for row in result:
            (ws_name, layer_name) = row[1].split(":")
            layer = Layer.objects.get(name=layer_name, datastore__workspace__name=ws_name)
            (fd, f) = tempfile.mkstemp(suffix=".JPG", prefix="img-gol-", dir=MEDIA_ROOT)
            output_file = os.fdopen(fd, "wb")
            try:
                output_file.write(row[3])
                res = LayerResource()
                res.id = row[0]
                res.feature = row[2]
                res.layer = layer
                res.path = f
                res.title = row[4]
                res.type = LayerResource.EXTERNAL_IMAGE
                res.created = timezone.now()
                res.save()
            finally:
                output_file.close()


    finally:
        conn.close()

def _get_image_row():
    server_resources = LayerResource.objects.filter(layer__name__in=layers, type=LayerResource.EXTERNAL_IMAGE)
    for r in server_resources:
        img_buffer = io.open(r.path, mode='rb')
        """
        img_buffer = open(r.path, mode='rb')
        imgblob = img.read()
        img.close()
        """
        
        thumb_buffer = BytesIO()
        img = Image.open(r.path)
        img.thumbnail([100, 100])
        img.save(thumb_buffer, "JPEG")
        #thumb_blob = thumb_buffer.getvalue()
        yield (r.id, r.layer, 'BLOB_IMAGE', r.title, r.feature, r.path, img_buffer, thumb_buffer)

def _copy_images2(layers, db_path):
    """
    Copies images for the provided layers from LayerResource to a SpatialiteDb
    """
    conn = sqlite3.connect(db_path)
    sql_create = """CREATE TABLE geopap_resource (id integer PRIMARY KEY NOT NULL, restable text, type integer, resname TEXT, rowidfk TEXT, respath TEXT, resblob BLOB, resthumb BLOB)"""
    conn.execute()
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO geopap_resource (id, restable, type, resname, rowidfk, respath, resblob, resthumb) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        cursor.executemany(sql, _get_image_row())
        cursor.commit()
    finally:
        conn.close()



def _copy_images(layers, db_path):
    """
    Copies images for the provided layers from LayerResource to a SpatialiteDb
    """
    server_resources = LayerResource.objects.filter(layer__name__in=layers, type=LayerResource.EXTERNAL_IMAGE)
    conn = sqlite3.connect(db_path)
    sql_create = """CREATE TABLE geopap_resource (id integer PRIMARY KEY NOT NULL, restable text, type integer, resname TEXT, rowidfk TEXT, respath TEXT, resblob BLOB, resthumb BLOB)"""
    conn.execute(sql_create)
    # some PRAMA for faster inserts
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO geopap_resource (id, restable, type, resname, rowidfk, respath, resblob, resthumb) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        for r in server_resources:
            # FIXME: we are loading in memory the whole image
            # We should investigate if we can pass an iterable to cursor.execute.
            # It seems to NOT be supported for the moment, but we can check again in future versions 
            thumb_buffer = BytesIO()
            img = Image.open(r.path)
            img.thumbnail([100, 100])
            img.save(thumb_buffer, "JPEG")
            
            img = open(r.path, mode='rb')
            img_bytes = img.read()
            img_buffer = buffer(img_bytes)
            img.close()
            #thumb_blob = thumb_buffer.getvalue()
            cursor.execute(sql, (r.id, r.layer.get_qualified_name(), 'BLOB_IMAGE', r.title, r.feature, r.path, img_buffer, buffer(thumb_buffer.getvalue())))
            img.close()
            thumb_buffer.close()
        conn.commit()

    finally:
        conn.close()


def _get_layer_conn(layer):
    try:
        conn_params = layer.datastore.connection_params
        params_dict = json.loads(conn_params)
        host = params_dict["host"]
        port = params_dict["port"]
        dbname = params_dict["database"]
        schema = params_dict["schema"]
        user = params_dict["user"]
        password = params_dict["passwd"]
        return gdaltools.PgConnectionString(host, port, dbname, schema, user, password)
    except:
        pass


def handle_uploaded_file(f):
    (destination, path) = tempfile.mkstemp(suffix='.sqlite', dir='/tmp')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    print path
    return path


def handle_uploaded_file_base64(fileupload):
    header="data:application/zip;base64,"
    if fileupload[0:len(header)]==header:
        fileupload = fileupload[len(header):].decode('base64')
    (destination, path) = tempfile.mkstemp(suffix='.sqlite', dir='/tmp')
    #destination = tempfile.TemporaryFile()
    asBytes = bytearray(fileupload, "unicode_internal")
    destination.write(asBytes)
    destination.close()
    print path
    return path


def handle_uploaded_file_raw(request):
    (fd_dest, path) = tempfile.mkstemp(suffix='.sqlite', dir='/tmp')
    destination = os.fdopen(fd_dest, "w", DEFAULT_BUFFER_SIZE)
    shutil.copyfileobj(request, destination, DEFAULT_BUFFER_SIZE)
    destination.close()
    print path
    return path

class ResourceReplacer():
    """
    Compares existing resources with the uploaded ones and performs and efficient
    update of the LayerResources tables, considering only deletions and insertions.
    """
    
    def __init__(self, db_path, layers):
        self.db_path = db_path
        self.layers = layers
        self.sqlite_conn = None
    
    def _get_sqlite_iterator(self):
        self.sqlite_conn = sqlite3.connect(self.db_path)
        cursor = self.sqlite_conn.cursor()
        sql = "SELECT id, restable, rowidfk, resblob, resname, respath FROM geopap_resource WHERE type = 'BLOB_IMAGE' ORDER BY id"
        return cursor.execute(sql)

    def process(self):
        """
        The strategy to follow is:
        - any resource id present in the sqlite and missing in the server is
        considered an insert
        - any resource id present in the server and missing in the sqlite is
        considered a deletion
        - if the ids are present in both sides, we consider this to be a
        replacement (deletion + insert) if the path field differs. Otherwise we
        consider to be the same resource and we ignore it 
        """
        try:
            sqlite_resources = self._get_sqlite_iterator()
            server_resources = LayerResource.objects.filter(layer__in=self.layers, type=LayerResource.EXTERNAL_IMAGE).order_by("id").iterator()

            sq_res = self._get_next(sqlite_resources)
            srv_res = self._get_next(server_resources)
            while sq_res or srv_res:
                if sq_res and srv_res:
                    if sq_res[0] == srv_res.id:
                        if sq_res[5] != srv_res.path:
                            self._remove_resource(srv_res)
                            self._insert(sq_res)
                        sq_res = self._get_next(sqlite_resources)
                        srv_res = self._get_next(server_resources)
                    elif sq_res[0] > srv_res.id:
                        self._remove_resource(srv_res)
                        srv_res = self._get_next(server_resources)
                    else:
                        self._insert(sq_res)
                        sq_res = self._get_next(sqlite_resources)
                elif sq_res:
                    self._insert(sq_res)
                    sq_res = self._get_next(sqlite_resources)
                else:
                    self._remove_resource(srv_res)
                    srv_res = self._get_next(server_resources)
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()

    def _remove_resource(self, resource):
        if os.path.isfile(resource.path):
            os.remove(resource.path)
        resource.delete()

    def _insert(self, newres):
        # FIXME: maybe we should process the resources by layer to avoid
        # getting the layer object again and again
        (ws_name, layer_name) = newres[1].split(":")
        layer = Layer.objects.get(name=layer_name, datastore__workspace__name=ws_name)
        
        (fd, f) = tempfile.mkstemp(suffix=".JPG", prefix="img-gol-", dir="/tmp/")
        output_file = os.fdopen(fd, "wb")
        try:
            output_file.write(newres[3])
            res = LayerResource()
            res.id = newres[0]
            res.feature = newres[2]
            res.layer = layer
            res.path = f
            res.title = newres[4]
            res.type = LayerResource.EXTERNAL_IMAGE
            res.save(force_insert=True)
        finally:
            output_file.close()

    def _get_next(self, iterator):
        """
        Returns the next object in the iterable or None if we have finished
        """
        try:
            return next(iterator)
        except StopIteration:
            return None


class TemporaryFileWrapper(tempfile._TemporaryFileWrapper):
    """
    This wrapper opens a file in a way that it ensures the file is deleted when
    is closed (in the same way as it is done by tempfile Python module).
    
    The wrappers offers a file-like object interface, so it can be used as a
    replacement of file objects.
    
    TemporaryFileWrapper is useful in scenarios when the file has to be opened
    and closed several times before being deleted, so it can not be created
    using tempfile.NamedTemporaryFile().
    
    TemporaryFileWrapper is based on tempfile._TemporaryFileWrapper, but the
    constructor of the first one expects a file path as parameter,
    while the second one expects an open file
    
    :param file_path: The path to the file to be opened
    :param binary_mode: True for specifying binary mode, false for text mode.
            It defaults to True
    """
    def __init__(self, file_path, binary_mode=True):
        if binary_mode:
            file = open(file_path, "rb")
        else:
            file = open(file_path, "r")
        tempfile._TemporaryFileWrapper.__init__(self, file, file_path)


    def close(self):
        # we can't use os.O_TEMPORARY flag if we are not creating the file,
        # so we need to implement close() also for windows
        if not self.close_called:
            self.close_called = True
            try:
                self.file.close()
            finally:
                if self.delete:
                    self.unlink(self.name)


    def __del__(self):
        # we can't use os.O_TEMPORARY flag if we are not creating the file,
        # so we need to implement __del__() also for windows
        self.close()


    def __exit__(self, exc, value, tb):
        # we can't use os.O_TEMPORARY flag if we are not creating the file,
        # so we need to implement __exit__() also for windows
        result = self.file.__exit__(exc, value, tb)
        self.close()
        return result


class LayerLockingException(BaseException):
    pass


class LayerNotLocked(LayerLockingException):
    """The requested layer lock does not exist"""
    
    def __init__(self, layer=None):
        self.layer = layer


class LayerLocked(LayerLockingException):
    """The layer already has a lock"""

    def __init__(self, layer=None):
        self.layer = layer