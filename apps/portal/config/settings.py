"""
Django settings for BKB Portal project.
Conforme al Plan de Implementación de BKB (Seguridad ASVS Nivel 2).
"""

import os
from pathlib import Path

from csp.constants import NONE, SELF
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Lee apps/portal/.env (local, nunca versionado). Lo que ya esté en el entorno tiene prioridad.
load_dotenv(BASE_DIR / '.env')

# Debug controlado por entorno (falso por defecto)
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

# Clave secreta: obligatoria salvo en desarrollo local (DEBUG=True)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            'Falta DJANGO_SECRET_KEY: con DJANGO_DEBUG=False el portal no arranca sin una '
            'clave real. Defínela en apps/portal/.env o en las variables del entorno.'
        )
    SECRET_KEY = 'django-insecure-bkb-solo-desarrollo-local'

# Sin valores por defecto: con DEBUG=True Django ya acepta localhost y 127.0.0.1
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Paquetes de terceros
    'csp',
    'axes',  # se activa en la tarea 7

    # Aplicaciones del portal
    'accounts',
    'documentos',
]

# Usuario propio (entra con correo). No se cambia después del primer migrate.
AUTH_USER_MODEL = 'accounts.Usuario'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Base de datos: PostgreSQL en producción / SQLite para desarrollo local
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Hashing de contraseñas robusto: Argon2id prioritario (ASVS 5.0)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalización
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Archivos estáticos y media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DigitalOcean Space (solo para firmar URLs; los archivos no pasan por Django)
SPACES_KEY = os.environ.get('SPACES_KEY', '')
SPACES_SECRET = os.environ.get('SPACES_SECRET', '')
SPACES_BUCKET = os.environ.get('SPACES_BUCKET', 'bkb-space')
SPACES_REGION = os.environ.get('SPACES_REGION', 'nyc3')
SPACES_ENDPOINT = os.environ.get('SPACES_ENDPOINT', 'https://nyc3.digitaloceanspaces.com')
# Todo lo que el portal escribe o firma vive bajo este prefijo. Vacío significaría todo el bucket.
SPACES_PREFIX = os.environ.get('SPACES_PREFIX', 'portal-dev/')
if not SPACES_PREFIX.endswith('/') or SPACES_PREFIX.startswith('/') or '..' in SPACES_PREFIX or SPACES_PREFIX == '/':
    raise ImproperlyConfigured(
        f"SPACES_PREFIX={SPACES_PREFIX!r} no es válido: debe ser una carpeta como 'portal-dev/' o 'portal/'."
    )
MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', '50'))

# Seguridad de Sesiones y Cookies (Plan Sección 5)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 43200  # 12 horas máximo absoluto
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
X_FRAME_OPTIONS = 'DENY'

# Content-Security-Policy estricta, sin 'unsafe-inline'.
# Las tareas 8 y 12 agregan el nonce del script del tema y el dominio del Space.
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': [SELF],
        'frame-ancestors': [NONE],
        'base-uri': [SELF],
        'form-action': [SELF],
        'object-src': [NONE],
    },
}

# Parámetros estrictos de producción activables vía SSL
if not DEBUG:
    # App Platform termina el HTTPS en su proxy: sin esto, SECURE_SSL_REDIRECT redirige sin fin.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Prefijo __Host-: el navegador solo lo acepta con Secure, Path=/ y sin Domain (docs/04).
    SESSION_COOKIE_NAME = '__Host-sessionid'
    CSRF_COOKIE_NAME = '__Host-csrftoken'
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Configuración de django-axes
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AXES_FAILURE_LIMIT = 5
AXES_LOCKOUT_TEMPLATE = None

# Rutas de autenticación
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
