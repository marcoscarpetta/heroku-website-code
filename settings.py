#
# Copyright (C) 2017-2018 Marco Scarpetta
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os
import configparser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(BASE_DIR, 'config.ini'))

SECRET_KEY = CONFIG["Secrets"]["secret_key"]

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'code.blog.apps.BlogConfig'
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

ROOT_URLCONF = 'code.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'resources', 'templates'),
            os.path.join(BASE_DIR, 'code', 'blog', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'code.context_processor.site_url',
            ],
        },
    },
]

WSGI_APPLICATION = 'code.wsgi.application'

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'resources', 'static'),
]

if "DEBUG" in os.environ:
    # Debug settings
    SITE_URL = "http://localhost:8000"
    SECURE_SITE_URL = "http://localhost:8000"

    DEBUG = True
    
    ALLOWED_HOSTS = []
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    # Heroku server settings
    import dj_database_url
    
    SITE_URL = CONFIG["Website"]["url"]
    SECURE_SITE_URL = CONFIG["Website"]["secure_url"]

    DEBUG = False
    
    INSTALLED_APPS.insert(0, 'whitenoise.runserver_nostatic')
    MIDDLEWARE.insert(0, 'whitenoise.middleware.WhiteNoiseMiddleware')

    DATABASES = {'default': dj_database_url.config(conn_max_age=500)}

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    ALLOWED_HOSTS = ['*']

    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
