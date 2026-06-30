# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

# Django settings for the GeoNode project.
import os

# Load more settings from a file called local_settings.py if it exists
try:
    from geonode_project.local_settings import *
#    from geonode.local_settings import *
except ImportError:
    from geonode.settings import *

#
# General Django development settings
#
PROJECT_NAME = "geonode_project"

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith("/"):
    SITEURL = "{}/".format(SITEURL)

SITENAME = os.getenv("SITENAME", "geonode_project")

# API key (PIN) untuk service Capaian FOLUR + Sitroom (read-only) ke DST Nasional.
# Default 123456; override via env DST_CAPAIAN_API_KEY di produksi.
DST_CAPAIAN_API_KEY = os.getenv("DST_CAPAIAN_API_KEY", "123456")

# Defines the directory that contains the settings file as the LOCAL_ROOT
# It is used for relative settings elsewhere.
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

WSGI_APPLICATION = "{}.wsgi.application".format(PROJECT_NAME)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "id")

if PROJECT_NAME not in INSTALLED_APPS:
    INSTALLED_APPS += (PROJECT_NAME,)

# Location of url mappings
ROOT_URLCONF = os.getenv("ROOT_URLCONF", "{}.urls".format(PROJECT_NAME))

# Additional directories which hold static files
# - Give priority to local geonode-project ones
STATICFILES_DIRS = [
    os.path.join(LOCAL_ROOT, "static"),
] + STATICFILES_DIRS

# Location of locale files
LOCALE_PATHS = (os.path.join(LOCAL_ROOT, "locale"),) + LOCALE_PATHS

TEMPLATES[0]["DIRS"].insert(0, os.path.join(LOCAL_ROOT, "templates"))
loaders = TEMPLATES[0]["OPTIONS"].get("loaders") or [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]
# loaders.insert(0, 'apptemplates.Loader')
TEMPLATES[0]["OPTIONS"]["loaders"] = loaders
TEMPLATES[0].pop("APP_DIRS", None)


PROJECT_FIXTURES = [
    # List project-related fixture files here, in the order they should be loaded.
]

# Django 4.0+ requires CSRF_TRUSTED_ORIGINS to match the request origin
_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = ["http://localhost", "http://127.0.0.1"]

# When serving over plain HTTP, Secure cookies are silently dropped by browsers
if not os.getenv("HTTPS_HOST", ""):
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

# After successful login, send users to the DST admin dashboard
LOGIN_REDIRECT_URL = "/dst-auth/dashboard/"

# Add Indonesian to MapStore language selector
# Override LANGUAGES after geonode import — geonode core filters env LANGUAGES
# against the original MAPSTORE_DEFAULT_LANGUAGES (no Indonesian), which would
# drop 'id' and break LANGUAGE_CODE='id'
MAPSTORE_DEFAULT_LANGUAGES = (
    ("id-ID", "Indonesia"),
    ("en-us", "English"),
)
LANGUAGES = MAPSTORE_DEFAULT_LANGUAGES
PROFILE_LANGUAGE_CHOICES = tuple((code.split("-")[0].lower(), label) for code, label in LANGUAGES)

# The language selector button shows the active language's native name via
# Django's {% get_language_info %} (LANG_INFO), which for 'id' defaults to
# "Bahasa Indonesia". Override it to display just "Indonesia".
import django.conf.locale  # noqa: E402

if "id" in django.conf.locale.LANG_INFO:
    django.conf.locale.LANG_INFO["id"] = {
        **django.conf.locale.LANG_INFO["id"],
        "name_local": "Indonesia",
    }

# Make Indonesian the default UI language on a visitor's first load.
# LocaleMiddleware otherwise follows the browser's Accept-Language header when
# no language cookie is set, so an English browser would see English. This
# custom middleware rewrites Accept-Language to LANGUAGE_CODE until the user
# explicitly picks a language (which sets the django_language cookie).
MIDDLEWARE = list(MIDDLEWARE)
_default_lang_mw = "{}.middleware.DefaultLanguageMiddleware".format(PROJECT_NAME)
if _default_lang_mw not in MIDDLEWARE:
    try:
        _locale_idx = MIDDLEWARE.index("django.middleware.locale.LocaleMiddleware")
    except ValueError:
        _locale_idx = len(MIDDLEWARE)
    MIDDLEWARE.insert(_locale_idx, _default_lang_mw)
MIDDLEWARE = tuple(MIDDLEWARE)
