import os
import environ
from pathlib import Path
from datetime import timedelta



# 1. Inicializamos la herramienta
env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Lectura del archivo .env según el settings activo
DJANGO_SETTINGS_MODULE = os.environ.get("DJANGO_SETTINGS_MODULE", "")
env_file = ".env.production" if DJANGO_SETTINGS_MODULE.endswith("settings.production") else ".env"
environ.Env.read_env(os.path.join(BASE_DIR, env_file))


SECRET_KEY = env('SECRET_KEY')


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'), 
        'PORT': env('DB_PORT', default='5432'),      
    }
}


# 4. CONFIGURACIÓN HIKVISION (Desde el Búnker)
HIKVISION_CONFIG = {
    'IP': env('HIK_IP'),
    'USER': env('HIK_USER'),
    'PASS': env('HIK_PASS'),
    'TIMEOUT': env.int('HIK_TIMEOUT', default=10), 
}

ATTENDANCE_WEBHOOK_KEY = env("ATTENDANCE_WEBHOOK_KEY")


CANCEL_PIN = env('CANCEL_PIN')



INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
    'rest_framework',
    'rest_framework_simplejwt',
    "django_apscheduler",
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_gym.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'my_gym.wsgi.application'






# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'es-ec'

TIME_ZONE = 'America/Guayaquil'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static',
]


# Custom user model
AUTH_USER_MODEL = 'core.User'



MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated', # Cerramos la puerta a desconocidos
    ),
}



SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8), # La llave dura 8 horas (tu jornada)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1), # El refresh dura 1 día
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',), # Importante para Axios
}


FRONTEND_URL = env("FRONTEND_URL", default="").rstrip("/")

WHATSAPP_ACCESS_TOKEN = env("WHATSAPP_ACCESS_TOKEN", default="")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID", default="")
WHATSAPP_WABA_ID = env("WHATSAPP_WABA_ID", default="")
WHATSAPP_TEST_TO = env("WHATSAPP_TEST_TO", default="") 
WHATSAPP_API_VERSION = env("WHATSAPP_API_VERSION", default="v22.0")
WHATSAPP_TEMPLATE_CREDENTIALS = env("WHATSAPP_TEMPLATE_CREDENTIALS", default="hello_world")
WHATSAPP_TEMPLATE_LANG = env("WHATSAPP_TEMPLATE_LANG", default="en_US")


# =========================
# EMAIL (SMTP)
# =========================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=5)