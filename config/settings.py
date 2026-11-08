import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── XAVFSIZLIK SOZLAMALARI ──────────────────────────────────────────────────
# Muhim: production uchun SECRET_KEY ni .env fayldan o'qing yoki
# muhit o'zgaruvchisi sifatida bering.
# Misol: export DJANGO_SECRET_KEY="sizning-maxfiy-kalitingiz"
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-dev-only-key-REPLACE-IN-PRODUCTION-" + "x" * 32,
)

# Production da: DEBUG=False, ALLOWED_HOSTS=[\"sizning-domeningiz.com\"]
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

_hosts_env = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _hosts_env.split(",") if h.strip()] or (
    ["*"] if DEBUG else ["localhost", "127.0.0.1"]
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "parking",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS":    [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME":   BASE_DIR / "parking.db",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "uz"
TIME_ZONE     = "Asia/Tashkent"
USE_I18N      = True
USE_TZ        = True

STATIC_URL  = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL          = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level":    "INFO",
            "class":    "logging.FileHandler",
            "filename": BASE_DIR / "parking_log.txt",
        },
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "parking": {
            "handlers":  ["file", "console"],
            "level":     "INFO",
            "propagate": False,
        },
    },
}
