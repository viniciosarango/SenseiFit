from .base import *
from environ import Env

env = Env()
env.read_env(str(BASE_DIR / ".env"))

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False

SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Email en consola (solo local)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "SenseiFit <no-reply@senseifit.local>"

# Email real por SMTP (local)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="SenseiFit <senseifit.app@gmail.com>")
#FRONTEND_URL = "http://localhost:5173"
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")


# WhatsApp Cloud API (local)
WHATSAPP_ACCESS_TOKEN = env("WHATSAPP_ACCESS_TOKEN", default="")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID", default="")
WHATSAPP_WABA_ID = env("WHATSAPP_WABA_ID", default="")
WHATSAPP_API_VERSION = env("WHATSAPP_API_VERSION", default="v22.0")
WHATSAPP_TEMPLATE_CREDENTIALS = env("WHATSAPP_TEMPLATE_CREDENTIALS", default="")

WHATSAPP_VERIFY_TOKEN = env("WHATSAPP_VERIFY_TOKEN", default="senseifit_verify_token")