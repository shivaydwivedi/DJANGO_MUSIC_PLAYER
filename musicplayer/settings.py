import os
from urllib.parse import urlparse

from decouple import config
from django.core.exceptions import ImproperlyConfigured


# Authoritative Sonica settings module for local development and test runs.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_csv(value):
    """Return a clean list from a comma-separated environment variable."""
    if value is None:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


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


def validate_runtime_settings(secret_key, debug, allowed_hosts):
    if not debug and not secret_key:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is False.')
    if not debug and not allowed_hosts:
        raise ImproperlyConfigured('ALLOWED_HOSTS must be set when DEBUG is False.')


# Local development defaults are intentionally easy to start. Production
# hardening is deferred, but unsafe production-like combinations fail fast.
DEBUG = config('DEBUG', default=True, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='sonica-local-development-secret-key')
ALLOWED_HOSTS = parse_csv(
    config('ALLOWED_HOSTS', default='localhost,127.0.0.1,[::1],testserver')
)
CSRF_TRUSTED_ORIGINS = parse_csrf_trusted_origins(
    config('CSRF_TRUSTED_ORIGINS', default='')
)
validate_runtime_settings(SECRET_KEY, DEBUG, ALLOWED_HOSTS)


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
