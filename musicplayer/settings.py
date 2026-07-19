import os
from urllib.parse import urlparse

from decouple import config
from django.core.exceptions import ImproperlyConfigured


# Authoritative Sonica settings module for local development and test runs.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_SECRET_KEY = 'sonica-local-development-secret-key'


def parse_csv(value):
    """Return a clean list from a comma-separated environment variable."""
    if value is None:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def parse_non_negative_int(value, setting_name):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured('{0} must be a non-negative integer.'.format(setting_name)) from exc
    if parsed < 0:
        raise ImproperlyConfigured('{0} must be a non-negative integer.'.format(setting_name))
    return parsed


def parse_csrf_trusted_origins(value):
    origins = parse_csv(value)
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ImproperlyConfigured(
                'CSRF_TRUSTED_ORIGINS values must be comma-separated absolute '
                'http:// or https:// origins.'
            )
    return origins


def validate_runtime_settings(
    secret_key,
    debug,
    allowed_hosts,
    csrf_trusted_origins,
    secure_hsts_seconds,
    secure_hsts_include_subdomains,
    secure_hsts_preload,
):
    if not debug and not secret_key:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is False.')
    if not debug and secret_key == LOCAL_SECRET_KEY:
        raise ImproperlyConfigured('SECRET_KEY must not use the local development fallback when DEBUG is False.')
    if not debug and (len(secret_key) < 50 or len(set(secret_key)) < 5 or secret_key.startswith('django-insecure-')):
        raise ImproperlyConfigured('SECRET_KEY must be at least 50 characters with enough randomness when DEBUG is False.')
    if not debug and not allowed_hosts:
        raise ImproperlyConfigured('ALLOWED_HOSTS must be set when DEBUG is False.')
    if not debug and '*' in allowed_hosts:
        raise ImproperlyConfigured('ALLOWED_HOSTS must not contain "*" when DEBUG is False.')
    if not debug:
        for origin in csrf_trusted_origins:
            if urlparse(origin).scheme != 'https':
                raise ImproperlyConfigured('CSRF_TRUSTED_ORIGINS must use https:// origins when DEBUG is False.')
    if secure_hsts_include_subdomains and secure_hsts_seconds == 0:
        raise ImproperlyConfigured('SECURE_HSTS_INCLUDE_SUBDOMAINS requires SECURE_HSTS_SECONDS greater than 0.')
    if secure_hsts_preload and secure_hsts_seconds == 0:
        raise ImproperlyConfigured('SECURE_HSTS_PRELOAD requires SECURE_HSTS_SECONDS greater than 0.')


# Local development defaults are intentionally easy to start. Production
# hardening is deferred, but unsafe production-like combinations fail fast.
DEBUG = config('DEBUG', default=True, cast=bool)
SECRET_KEY = config('SECRET_KEY', default=LOCAL_SECRET_KEY)
ALLOWED_HOSTS = parse_csv(
    config('ALLOWED_HOSTS', default='localhost,127.0.0.1,[::1],testserver')
)
CSRF_TRUSTED_ORIGINS = parse_csrf_trusted_origins(
    config('CSRF_TRUSTED_ORIGINS', default='')
)

SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = parse_non_negative_int(config('SECURE_HSTS_SECONDS', default='0'), 'SECURE_HSTS_SECONDS')
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
SECURE_REFERRER_POLICY = config('SECURE_REFERRER_POLICY', default='strict-origin-when-cross-origin')
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='DENY')
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')
TRUST_X_FORWARDED_PROTO = config('TRUST_X_FORWARDED_PROTO', default=False, cast=bool)
USE_X_FORWARDED_HOST = config('USE_X_FORWARDED_HOST', default=False, cast=bool)
if TRUST_X_FORWARDED_PROTO:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

validate_runtime_settings(
    SECRET_KEY,
    DEBUG,
    ALLOWED_HOSTS,
    CSRF_TRUSTED_ORIGINS,
    SECURE_HSTS_SECONDS,
    SECURE_HSTS_INCLUDE_SUBDOMAINS,
    SECURE_HSTS_PRELOAD,
)


DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # allauth apps
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # apps
    'authentication.apps.AuthenticationConfig',
    'musicapp.apps.MusicappConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'musicplayer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'musicplayer.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

SITE_ID = 1

ACCOUNT_EMAIL_VERIFICATION = 'none'

LOGIN_REDIRECT_URL = 'index'

ENABLE_GOOGLE_AUTH = config('ENABLE_GOOGLE_AUTH', default=False, cast=bool)

SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
        }
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
