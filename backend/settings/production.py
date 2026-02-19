from .base import *
from environ import Env

env = Env()

# =====================================================
# CORE
# =====================================================

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")


# =====================================================
# CORS / CSRF
# =====================================================

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

CORS_ALLOW_CREDENTIALS = True


# =====================================================
# SSL / PROXY
# =====================================================

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True


# =====================================================
# COOKIES
# =====================================================

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Vue necesita leerla
CSRF_COOKIE_SAMESITE = "Lax"


# =====================================================
# SECURITY HEADERS
# =====================================================

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# =====================================================
# STATIC FILES
# =====================================================

STATIC_ROOT = BASE_DIR / "staticfiles"
