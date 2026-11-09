

import os
import sys

from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


TESTING = "test" in sys.argv[1:2]
ENVIRONMENT = "test" if TESTING else os.environ.get(
    "ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
# DEBUG = True shows detailed error pages with your code and settings. It must be False in production.
DEBUG = ENVIRONMENT == "development"

DEV_SECRET_KEY = "change-me-dev-only-not-for-production-use"

# SECRET_KEY signs cookies, sessions and password-reset links. Anyone who has it can forge them, so in production it
# must come from an environment variable.
SECRET_KEY = os.environ.get("SECRET_KEY", DEV_SECRET_KEY)

if IS_PRODUCTION and SECRET_KEY == DEV_SECRET_KEY:
    raise ImproperlyConfigured(
        "Set SECRET_KEY to a long random value in production.")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-=@m2ln^$c*tm8e9f-=@5%ihpr9=!uru!bd1gb_=^a+8zhktdzt'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS", "localhost, 127.0.0.1,testserver").split(",")
if render_host := os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(render_host)


# Application definition
# INSTALLED_APPS: every app Django loads: its models, migrations, admin pages and templates. Your own apps must be listed here to be loaded by Django.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "channels",
    # our modules: one Django app each
    "modules.core",
    "modules.accounts",
    "modules.clients",
    "modules.invoices",
    "modules.payments",
    "modules.events",
    "modules.notifications",
    "modules.realtime",
    "modules.ai",
    "modules.rates",
    "modules.dashboard",
]

# MIDDLEWARE: code that runs around every request, top to bottom on the way in and bottom to top on the way out
MIDDLEWARE = [
    "modules.core.middleware.RequestLoggingMiddleware",
    "modules.core.middleware.HealthCheckMiddleware",
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves the static files (the admin's CSS and JavaScript) straight from gunicorn, so you don't need
    # a separate web server. It goes right after SecurityMiddleware.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ROOT_URLCONF: the file where URL matching starts.
ROOT_URLCONF = 'config.urls'

# ASGI_APPLICATION: the app uvicorn runs (config/asgi.py). ASGI can serve WebSockets, which WSGI can't.
ASGI_APPLICATION = "config.asgi.application"

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


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# DATABASES: which database to use. SQLite is a single file, perfect for learning; production uses Postgres.

DATABASES = {
    "default": dj_database_url.config(
        default="postgresql://postgres:postgres@localhost:5432/billing", conn_max_age=600, conn_health_checks=True
    )
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
# USE_TZ = True: store every date and time in UTC and keep them timezone-aware. Always leave it on.

USE_TZ = True

# if items: empty lists, empty strings, 0 and None all count as false ("truthiness").
if TESTING:
    # The tests use their own Redis database, and never real keys: no money moves, no AI quota is used.
    os.environ["REDIS_URL"] = os.environ.get(
        "TEST_REDIS_URL", "redis://localhost:6379/1")
    os.environ.update(PAYSTACK_SECRET_KEY="",
                      AI_API_KEY="", EMAIL_BACKEND="memory")
    # PASSWORD_HASHERS: a fast hasher for tests only. Real hashing is slow on purpose, which would make every test
    # that registers a user slow too.
    # PasswordHash.recommended(): Argon2, a slow one-way hash made for passwords.
    # fast, and only ever used in tests
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

    # Redis does three jobs: the cache (dashboard, exchange rates, rate-limit counters), and the channel layer
# that carries live messages from the worker to the browsers' WebSockets.
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
# CACHES: where cache.get and cache.set keep data. LocMemCache is memory inside one process; Redis is shared by
# every server and survives restarts.
CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}}
# CHANNEL_LAYERS: how Channels passes messages between processes (the worker and every web server) through Redis.
CHANNEL_LAYERS = {"default": {
    "BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [REDIS_URL]}}}


# REST_FRAMEWORK: one dict with every DRF setting: how users log in, who may call views, pagination and rate limits.
REST_FRAMEWORK = {
    # DEFAULT_AUTHENTICATION_CLASSES: how DRF finds out who is calling, tried in order. Token reads the
    # Authorization header; Session reads the browser cookie (for the browsable API).
    "DEFAULT_AUTHENTICATION_CLASSES": ["modules.accounts.authentication.CookieJWTAuthentication"],
    # DEFAULT_PERMISSION_CLASSES: who may call a view unless the view says otherwise. IsAuthenticated means logged-
    # in users only (others get 401).
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # DEFAULT_RENDERER_CLASSES: answer in JSON only (no browsable HTML pages for this API).
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    # EXCEPTION_HANDLER: our function that shapes every error response (core/errors.py).
    "EXCEPTION_HANDLER": "modules.core.errors.api_exception_handler",
    # COERCE_DECIMAL_TO_STRING: False sends Decimal values as JSON numbers (2.5) instead of strings ("2.50"),
    # matching what the React app expects.
    # quantities go out as numbers (2.5), like the FastAPI version
    "COERCE_DECIMAL_TO_STRING": False,
    # DEFAULT_THROTTLE_RATES: how many requests each throttle scope allows. Over the limit, DRF answers 429 Too Many
    # Requests.
    "DEFAULT_THROTTLE_RATES": {"login": "10/minute", "ai": "30/hour"},
    # UNAUTHENTICATED_USER: None means request.user is None when nobody is logged in.
    # None is Python's null.
    "UNAUTHENTICATED_USER": None,
    # TEST_REQUEST_DEFAULT_FORMAT: tests send JSON unless they say otherwise.
    # self.client.get(url, params) / .post(url, data, format="json"): send a request to the app in memory, no server
    # needed.
    # self is the current object, like `this` in C#. Python makes it the first parameter of every method; use self.x
    # to reach its fields.
    # self.client.post(url, data) in tests sends JSON
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
# STATIC_ROOT: the folder `collectstatic` copies every app's static files into, for production.
STATIC_ROOT = BASE_DIR / "staticfiles"
FRONTEND_DIST = BASE_DIR / "frontend_dist"

# .exists(): asks the database "is there at least one row?". Faster than loading rows to count them.
# WHITENOISE_ROOT: WhiteNoise also serves the files in this folder at the site root, so the built React app's
# /assets/... and /favicon.svg just work.
WHITENOISE_ROOT = FRONTEND_DIST if FRONTEND_DIST.exists() else None
# STORAGES: where files are kept. WhiteNoise's storage compresses the static files and puts a hash in each name, so
# browsers can cache them forever.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}


# Email: printed in the terminal, sent through SMTP (Mailpit locally), or kept in memory by the tests.
EMAIL_BACKENDS = {
    "console": "django.core.mail.backends.console.EmailBackend",
    "smtp": "django.core.mail.backends.smtp.EmailBackend",
    "memory": "django.core.mail.backends.locmem.EmailBackend",
}

EMAIL_BACKEND_NAME = os.environ.get("EMAIL_BACKEND", "console")
# MAILERS: Django 6.1's email settings: which backend sends the mail (console, SMTP, or memory for tests) and its
# options.


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    "default": {
        "BACKEND": EMAIL_BACKENDS[EMAIL_BACKEND_NAME],
        "OPTIONS": (
            # int(x): turn x (often text) into a whole number, or raise ValueError if it can't.
            {"host": os.environ.get("SMTP_HOST", "localhost"), "port": int(
                os.environ.get("SMTP_PORT", "1025"))}
            if EMAIL_BACKEND_NAME == "smtp"
            else {}
        ),
    }
}

# DEFAULT_FROM_EMAIL: the From address on emails we send.
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_FROM", "oluwayemifisayo@gmail.com")


# The app's own settings.
APP_NAME = "Freelancer Billing Platform"
FRONTEND_URL = os.environ.get("FRONTEND_URL") or os.environ.get(
    "RENDER_EXTERNAL_URL") or "http://localhost:5173"
ACCESS_TOKEN_MINUTES = 60 * 24
# empty = the fake gateway, no real money moves
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
# empty = template answers instead of AI
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_BASE_URL = os.environ.get(
    "AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
AI_MODEL = os.environ.get("AI_MODEL", "gemini-2.5-flash")
RATES_BASE_URL = os.environ.get(
    "RATES_BASE_URL", "https://open.er-api.com/v6/latest")


# LOGGING: send log messages, including the full error of every 500, to the terminal. Render shows the terminal as
# your logs. Without this, production errors are silent.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "modules.core.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": "WARNING" if TESTING else "INFO"},
    # Tests answer lots of 404s and 409s on purpose; only show real errors while they run.
    "loggers": {"django.request": {"level": "ERROR"}} if TESTING else {},
}

if IS_PRODUCTION:
    # Render ends HTTPS at its proxy and passes the request on with X-Forwarded-Proto: https.
    # SECURE_PROXY_SSL_HEADER: Render ends HTTPS at its proxy and passes the request on with X-Forwarded-Proto:
    # https. This tells Django to trust that header, so it knows the request was secure.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # SECURE_SSL_REDIRECT: send anyone using http:// to https://.
    SECURE_SSL_REDIRECT = True
    # HSTS: tells browsers to use only HTTPS for this site for the next 30 days, even if someone types http://.
    # browsers use only HTTPS for this site for 30 days
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    # SESSION_COOKIE_SECURE / CSRF_COOKIE_SECURE: only send these cookies over HTTPS.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [FRONTEND_URL]
