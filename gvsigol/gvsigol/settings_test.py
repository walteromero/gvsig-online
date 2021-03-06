# -*- coding: utf-8 -*-

'''
    gvSIG Online.
    Copyright (C) 2010-2017 SCOLAB.

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
@author: Javier Rodrigo <jrodrigo@scolab.es>
'''

import os
import django.conf.locale
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
if '__file__' in globals():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.join(os.path.abspath(os.getcwd()), "gvsigol")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '##s#jx5ildpkavpi@tbtl0fvj#(np#hyckdg*q#1mu%ovr8$t_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_jenkins',
]

PROJECT_APPS = [
    'gvsigol_auth',
    'gvsigol_services',
    'gvsigol_symbology',
    'gvsigol_filemanager',
    'gvsigol_core',
    ##GVSIG_ONLINE_APPS##
]
INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.PersistentRemoteUserMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CRONTAB_ACTIVE = False
ROOT_URLCONF = 'gvsigol.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'gvsigol_auth/templates'),
            os.path.join(BASE_DIR, 'gvsigol_core/templates'),
            os.path.join(BASE_DIR, 'gvsigol_services/templates'),
            os.path.join(BASE_DIR, 'gvsigol_symbology/templates'),
            os.path.join(BASE_DIR, 'gvsigol_filemanager/templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'gvsigol_core.context_processors.global_settings',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.i18n',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'gvsigol.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.contrib.gis.db.backends.postgis',
#        #'ENGINE': 'django.db.backends.postgresql_psycopg2',
#        'NAME': 'gvsigonline_v2',
#        'USER': 'postgres',
#        'PASSWORD': 'postgres',
#        'HOST': 'localhost',
#        'PORT': '5432',
#    }
#}
POSTGIS_VERSION = (2, 1, 2)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase',
    }
}

AUTH_WITH_REMOTE_USER = False

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

GVSIGOL_LDAP = {
    'ENABLED': False,
    'HOST':'devel.gvsigonline.com',
    'PORT': '389',
    'DOMAIN': 'dc=test,dc=gvsigonline,dc=com',
    'USERNAME': 'cn=admin,dc=test,dc=gvsigonline,dc=com',
    'PASSWORD': 'gvsigonline',
    'AD': ''
}

AUTHENTICATION_BACKENDS = (
    #'django.contrib.auth.backends.RemoteUserBackend',
    #'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

EXTRA_LANG_INFO = {
    'va': {
        'bidi': False,
        'code': u'va',
        'name': u'Valencian',
        'name_local': u'Valencian'
    },
}

# Add custom languages not provided by Django
LANG_INFO = dict(django.conf.locale.LANG_INFO.items() + EXTRA_LANG_INFO.items())
django.conf.locale.LANG_INFO = LANG_INFO

LANGUAGES = (
    ('es', _('Spanish')),
    ('va', _('Valencian')),
    ('ca', _('Catalan')), 
    ('en', _('English')),   
)
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'gvsigol/locale'),
    os.path.join(BASE_DIR, 'gvsigol_core/locale'),
    os.path.join(BASE_DIR, 'gvsigol_auth/locale'),
    os.path.join(BASE_DIR, 'gvsigol_services/locale'),
    os.path.join(BASE_DIR, 'gvsigol_symbology/locale'),
    os.path.join(BASE_DIR, 'gvsigol_filemanager/locale'),
    os.path.join(BASE_DIR, 'gvsigol_app_dev/locale'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_worldwind/locale'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_shps_folder/locale'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_geocoding/locale'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_etl/locale'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_edition/locale'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_graphiccapture/locale')
)

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
LOGOUT_PAGE_URL = '/gvsigonline/'

# Email settings
EMAIL_BACKEND_ACTIVE = False
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.yourdomain.org'
EMAIL_HOST_USER = 'gvsigonline@yourdomain.org'
EMAIL_HOST_PASSWORD = 'yourpass'
EMAIL_PORT = 587
SITE_ID=1

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
BASE_URL = 'https://localhost'
MEDIA_ROOT = '/var/www/media/'
MEDIA_URL = 'https://localhost/media/'
STATIC_URL = '/gvsigonline/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'gvsigol_core/static'),
    os.path.join(BASE_DIR, 'gvsigol_auth/static'),
    os.path.join(BASE_DIR, 'gvsigol_services/static'),
    os.path.join(BASE_DIR, 'gvsigol_symbology/static'),
    os.path.join(BASE_DIR, 'gvsigol_filemanager/static'),
    os.path.join(BASE_DIR, 'gvsigol_app_dev/static'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_worldwind/static'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_shps_folder/static'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_geocoding/static'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_etl/static'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_edition/static'),
    os.path.join(BASE_DIR, 'gvsigol_plugin_graphiccapture/static')
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'compressor.finders.CompressorFinder',
)

GVSIGOL_VERSION = '2.3.4'

GVSIGOL_USERS_CARTODB = {
    'dbhost': 'localhost',
    'dbport': '5432',
    'dbname': 'gvsigonline_v2',
    'dbuser': 'postgres',
    'dbpassword': 'postgres'
}

PUBLIC_VIEWER = True

GEOSERVER_PATH = '/gs-local'
FRONTEND_URL = 'https://localhost'

GVSIGOL_SERVICES = {
    'ENGINE':'geoserver',
    'URL': 'https://localhost/gs-local',
    'USER': 'admin',
    'PASSWORD': 'geoserver',
    'CLUSTER_NODES':[],
    'SUPPORTED_TYPES': (
                        ('v_PostGIS', _('PostGIS vector')),
                        #('v_SHP', _('Shapefile folder')),                        
                        ('c_GeoTIFF', _('GeoTiff')),
                        ('e_WMS', _('Cascading WMS')),
    ),
    # if MOSAIC_DB entry is omitted, mosaic indexes will be stored as SHPs
    'MOSAIC_DB': {
                  'host': 'localhost',
                  'port': '5432',
                  'database': 'gvsigonline_v2',
                  'schema': 'imagemosaic',
                  'user': 'postgres',
                  'passwd': 'postgres'
    },
    # NOTE: we are migrating gdal_tools to the external library pygdaltools
    # OGR path is only necessary if different from the one defined on gdal_tools.OGR2OGR_PATH
    # In the future we will only need GDALTOOLS_BASEPATH variable
    'OGR2OGR_PATH': '/usr/bin/ogr2ogr',
    'GDALTOOLS_BASEPATH': '/usr/bin'
}

TILE_SIZE = 256

# Must be a valid iconv encoding name. Use iconv --list on Linux to see valid names 
SUPPORTED_ENCODINGS = [ "LATIN1", "UTF-8", "ISO-8859-15", "WINDOWS-1252"]
USE_DEFAULT_SUPPORTED_CRS = True
SUPPORTED_CRS = {
    '3857': {
        'code': 'EPSG:3857',
        'title': 'WGS 84 / Pseudo-Mercator',
        'definition': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs',
        'units': 'meters'
    },
    '900913': {
        'code': 'EPSG:900913',
        'title': 'Google Maps Global Mercator -- Spherical Mercator',
        'definition': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs',
        'units': 'meters'
    },
    '4326': {
        'code': 'EPSG:4326',
        'title': 'WGS84',
        'definition': '+proj=longlat +datum=WGS84 +no_defs +axis=neu',
        'units': 'degrees'
    },
    '4258': {
        'code': 'EPSG:4258',
        'title': 'ETRS89',
        'definition': '+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs +axis=neu',
        'units': 'degrees'
    },
    '25830': {
        'code': 'EPSG:25830',
        'title': 'ETRS89 / UTM zone 30N',
        'definition': '+proj=utm +zone=30 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs',
        'units': 'meters'
    },
    '25829': {
        'code': 'EPSG:25829',
        'title': 'ETRS89 / UTM zone 29N',
        'definition': '+proj=utm +zone=30 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs',
        'units': 'meters'
    }
}

GVSIGOL_TOOLS = {
    'get_feature_info_control': {
        'private_fields_prefix': '_'
    },
    'attribute_table': {
        'private_fields_prefix': '_',
        'show_search': True
    }
}

GVSIGOL_ENABLE_ENUMERATIONS = True

GVSIGOL_BASE_LAYERS = {
    'bing': {
        'active': False,
        'key': 'Ak-dzM4wZjSqTlzveKz5u0d4IQ4bRzVI309GxmkgSVr1ewS6iPSrOvOKhA-CJlm3'
    }
}

#skin-blue
#skin-blue-light
#skin-red
#skin-red-light
#skin-black
#skin-black-light
#skin-green
#skin-green-light
#skin-purple
#skin-purple-light
#skin-yellow
#skin-yellow-light
GVSIGOL_SKIN = "skin-blue"

FILEMANAGER_DIRECTORY = os.path.join(MEDIA_ROOT, 'data')
FILEMANAGER_MEDIA_ROOT = os.path.join(MEDIA_ROOT, FILEMANAGER_DIRECTORY)
FILEMANAGER_MEDIA_URL = os.path.join(MEDIA_URL, FILEMANAGER_DIRECTORY)
FILEMANAGER_STORAGE = FileSystemStorage(location=FILEMANAGER_MEDIA_ROOT, base_url=FILEMANAGER_MEDIA_URL, file_permissions_mode=0o666)

CONTROL_FIELDS = [{
                'name': 'modified_by',
                'type': 'character_varying'
                },{
                'name': 'last_modification',
                'type': 'date'
                }]

BASELAYER_SUPPORTED_TYPES = ['WMS', 'WMTS', 'XYZ', 'Bing', 'OSM']

WMTS_MAX_VERSION = '1.0.0'
WMS_MAX_VERSION = '1.3.0'
BING_LAYERS = ['Road','Aerial','AerialWithLabels']
