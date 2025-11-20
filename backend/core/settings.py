"""
Django settings for core project.
"""

from pathlib import Path
import os
import logging
import dj_database_url

logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / 'api.log'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # Para permitir peticiones desde React
    'rest_framework',  # Django REST Framework
    'channels',
    'django_celery_beat',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir archivos estáticos en producción
    'corsheaders.middleware.CorsMiddleware',  # CORS debe estar antes de CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Configuración de base de datos
# En producción (Render): usar PostgreSQL si DATABASE_URL está disponible
# En desarrollo: usar SQLite
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'es-es'

# Configuración de zona horaria - sincronizar con el reloj del equipo
# TOTP usa tiempo UTC internamente, pero Django debe estar configurado correctamente
# Para sincronización precisa, usar UTC y asegurar que el reloj del sistema esté sincronizado
import os
TIME_ZONE = 'UTC'  # TOTP funciona mejor con UTC
# IMPORTANTE: Asegúrate de que el reloj de tu sistema esté sincronizado con un servidor NTP
# En Windows: w32tm /config /manualpeerlist:"time.windows.com" /syncfromflags:manual
# En Linux: sudo ntpdate -s time.nist.gov

USE_I18N = True

USE_TZ = True  # Usar timezone-aware datetimes


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'api:login'
LOGIN_REDIRECT_URL = 'api:board'
LOGOUT_REDIRECT_URL = 'api:login'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} ({module}:{lineno}) - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_FILE_PATH),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuración de Channel Layers para WebSockets
# InMemoryChannelLayer funciona bien para desarrollo con un solo proceso
# Para producción con múltiples workers, usar Redis:
# 'BACKEND': 'channels_redis.core.RedisChannelLayer',
# 'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'send-task-reminders-daily': {
        'task': 'api.tasks.send_due_date_reminders',
        'schedule': 60.0 * 60.0 * 24.0,  # cada 24 horas (en segundos)
        # Para pruebas, puedes usar: crontab(hour=9, minute=0) para ejecutar a las 9 AM diariamente
    },
    'send-board-reminders-daily': {
        'task': 'api.tasks.send_board_reminders_to_all_users',
        'schedule': 60.0 * 60.0 * 24.0,  # cada 24 horas (en segundos)
        # Envía recordatorios a todos los usuarios del tablero diariamente
        # Por defecto: vencidas y 1-3 días habilitados, 4-7 días deshabilitado
    },
}

# Configuración de correo electrónico
# Por defecto usa SMTP. Para desarrollo local, puedes cambiar a 'console' backend
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

# Configuración SMTP
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@kanban.local')

# Si no hay configuración SMTP, usar backend de consola como fallback
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    import warnings
    warnings.warn("EMAIL_HOST_USER o EMAIL_HOST_PASSWORD no configurados. Usando backend de consola para desarrollo.")
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuración CORS para permitir peticiones desde React
# OPCIÓN B → Configurar CORS + Cookies
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173'
).split(',')

# Orígenes confiables para CSRF
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173'
).split(',')

# Configuración de cookies de sesión
# En producción, usar SameSite='None' y Secure=True para HTTPS
USE_HTTPS = os.getenv('USE_HTTPS', 'False').lower() == 'true'
SESSION_COOKIE_SAMESITE = "None" if USE_HTTPS else "Lax"
SESSION_COOKIE_SECURE = USE_HTTPS  # True en producción con HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN', None)
SESSION_COOKIE_PATH = '/'  # Path para la cookie
CSRF_COOKIE_SAMESITE = "None" if USE_HTTPS else "Lax"
CSRF_COOKIE_SECURE = USE_HTTPS  # True en producción con HTTPS
CSRF_COOKIE_HTTPONLY = False  # Necesario para que JavaScript pueda leerlo
CSRF_COOKIE_DOMAIN = os.getenv('CSRF_COOKIE_DOMAIN', None)

# Métodos HTTP permitidos
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Headers permitidos
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Exponer headers en la respuesta
CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrftoken',
]

# Configuración de Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

