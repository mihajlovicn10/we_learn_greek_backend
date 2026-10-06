from pathlib import Path
import os
from datetime import timedelta

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None or value == '':
        return default
    return value.lower() in ('true', '1', 'yes')


def _env_list(name: str, default: str = '') -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


AUTH_USER_MODEL = 'we_learn_greek.User'
ROOT_URLCONF = 'we_learn_greek.urls'

# Production-safe by default: DEBUG must be switched on explicitly (see .env.example).
DEBUG = _env_bool('DEBUG', False)

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is off.')
    SECRET_KEY = 'dev-insecure-key-for-local-development-only'

ALLOWED_HOSTS = _env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')

INSTALLED_APPS = [
    'we_learn_greek.admin_site.ThrottledAdminConfig',  # replaces django.contrib.admin
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'drf_yasg',
    'corsheaders',
    'conjugator',
    'declinator',
    'dictionary',
    'greek_to_greek',
    'transparrent',
    'we_learn_greek',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # Deny by default; public views opt in with permission_classes = [AllowAny].
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'we_learn_greek.pagination.StandardPagination',
    'PAGE_SIZE': 12,
    # Counters live in the default cache (shared via Postgres in production, see CACHES).
    'DEFAULT_THROTTLE_RATES': {
        'auth': os.environ.get('AUTH_THROTTLE_RATE', '10/min'),                 # login, register
        'token': os.environ.get('TOKEN_THROTTLE_RATE', '30/min'),               # refresh, logout
        'admin_login': os.environ.get('ADMIN_LOGIN_THROTTLE_RATE', '5/min'),
        # Word content is the product: slow down bulk copying without bothering learners.
        'content_burst': os.environ.get('CONTENT_BURST_THROTTLE_RATE', '120/min'),
        'content_sustained': os.environ.get('CONTENT_SUSTAINED_THROTTLE_RATE', '2000/day'),
    },
    # Number of proxies in front of the app that append to X-Forwarded-For. Leave unset
    # until verified on the host; a wrong value makes all clients share one IP bucket.
    'NUM_PROXIES': int(os.environ['NUM_PROXIES']) if os.environ.get('NUM_PROXIES') else None,
}

# The frontend sends JWTs in the Authorization header, so no cookies cross origins.
CORS_ALLOWED_ORIGINS = _env_list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_ALL_ORIGINS = DEBUG and not CORS_ALLOWED_ORIGINS
CORS_ALLOW_CREDENTIALS = False
# Browsers hide non-safelisted response headers from cross-origin JS. The frontend reads
# Retry-After on 429s to tell the user how long to wait.
CORS_EXPOSE_HEADERS = ['Retry-After']
CSRF_TRUSTED_ORIGINS = _env_list('CSRF_TRUSTED_ORIGINS')

if not DEBUG:
    # Render terminates TLS at its proxy and forwards the original scheme in this header.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = _env_bool('SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '3600'))
    SECURE_REFERRER_POLICY = 'same-origin'

# HSTS includeSubDomains/preload are for a domain we own; on *.onrender.com the parent
# domain belongs to Render. Revisit when moving to a custom domain.
SILENCED_SYSTEM_CHECKS = ['security.W005', 'security.W021']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

def _postgres_ssl_required(database_url: str) -> bool:
    """Hosted Postgres (Render, Neon) needs SSL; local Docker does not."""
    local_markers = ('@localhost', '@127.0.0.1', '@db:')
    if any(marker in database_url for marker in local_markers):
        return False
    return os.environ.get('DATABASE_SSL_REQUIRE', 'true').lower() in ('true', '1', 'yes')


_database_url = os.environ.get('DATABASE_URL')
if _database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            ssl_require=_postgres_ssl_required(_database_url),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

if DEBUG:
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
else:
    # Shared across gunicorn workers so rate limits hold globally. Requires
    # `manage.py createcachetable` (build.sh runs it; the test runner does it itself).
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache',
            'OPTIONS': {'MAX_ENTRIES': 50000},
        }
    }

# Admin is needed to manage content until word data moves to JSON. Set ADMIN_ENABLED=false
# to remove it entirely, and ADMIN_URL to move it off the well-known path.
ADMIN_ENABLED = _env_bool('ADMIN_ENABLED', True)
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/').strip('/') + '/'

SIMPLE_JWT = {
    # Short-lived access tokens: a blacklisted refresh token stops new ones being issued,
    # but an access token already handed out stays valid until it expires.
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    # Every refresh returns a new refresh token and blacklists the old one.
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    # Tokens carry a password hash claim, so changing the password revokes them all.
    'CHECK_REVOKE_TOKEN': True,
    'UPDATE_LAST_LOGIN': True,
}

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
