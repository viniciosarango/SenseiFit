from .base import *
from environ import Env

env = Env()

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

