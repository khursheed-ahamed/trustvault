"""Django settings for the TrustVault project."""
import os
import secrets
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value.")


def env_list(name):
    return [
        value.strip()
        for value in os.environ.get(name, "").split(",")
        if value.strip()
    ]


PRODUCTION = os.environ.get("DJANGO_ENV", "development").strip().lower() == "production"
DEBUG = env_bool("DEBUG", default=not PRODUCTION)
if PRODUCTION and DEBUG:
    raise ImproperlyConfigured("DEBUG must be False when DJANGO_ENV=production.")

SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if PRODUCTION:
        raise ImproperlyConfigured("SECRET_KEY must be set in production.")
    SECRET_KEY = secrets.token_urlsafe(50)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    if PRODUCTION:
        raise ImproperlyConfigured("ALLOWED_HOSTS must be set in production.")
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "documents",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]
if PRODUCTION:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "trustvault.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "trustvault.wsgi.application"

TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Kolkata")
USE_TZ = True

database_url = os.environ.get("DATABASE_URL", "").strip()
if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            ssl_require=PRODUCTION,
        )
    }
    if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
        raise ImproperlyConfigured("DATABASE_URL must use PostgreSQL.")
elif PRODUCTION:
    raise ImproperlyConfigured("DATABASE_URL must point to PostgreSQL in production.")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "document_dashboard"
LOGOUT_REDIRECT_URL = "login"

MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

cloud_storage_values = {
    "access_key": os.environ.get("AWS_ACCESS_KEY_ID", "").strip(),
    "secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip(),
    "bucket_name": os.environ.get("AWS_STORAGE_BUCKET_NAME", "").strip(),
}
cloud_storage_requested = any(cloud_storage_values.values())
if PRODUCTION and not cloud_storage_requested:
    raise ImproperlyConfigured(
        "Private S3-compatible storage must be configured in production."
    )
if cloud_storage_requested:
    missing_storage_values = [
        name
        for name, value in (
            ("AWS_ACCESS_KEY_ID", cloud_storage_values["access_key"]),
            ("AWS_SECRET_ACCESS_KEY", cloud_storage_values["secret_key"]),
            ("AWS_STORAGE_BUCKET_NAME", cloud_storage_values["bucket_name"]),
        )
        if not value
    ]
    if missing_storage_values:
        raise ImproperlyConfigured(
            "Missing private storage settings: " + ", ".join(missing_storage_values)
        )

    default_storage = {
        "BACKEND": "documents.storage.PrivateS3Storage",
        "OPTIONS": {
            "access_key": cloud_storage_values["access_key"],
            "secret_key": cloud_storage_values["secret_key"],
            "bucket_name": cloud_storage_values["bucket_name"],
            "default_acl": None,
            "querystring_auth": True,
            "custom_domain": None,
            "file_overwrite": False,
        },
    }
    endpoint_url = os.environ.get("AWS_S3_ENDPOINT_URL", "").strip()
    region_name = os.environ.get("AWS_S3_REGION_NAME", "").strip()
    signature_version = os.environ.get("AWS_S3_SIGNATURE_VERSION", "").strip()
    if endpoint_url:
        default_storage["OPTIONS"]["endpoint_url"] = endpoint_url
    if region_name:
        default_storage["OPTIONS"]["region_name"] = region_name
    if signature_version:
        default_storage["OPTIONS"]["signature_version"] = signature_version
else:
    default_storage = {
        "BACKEND": "documents.storage.PrivateFileSystemStorage",
        "OPTIONS": {"location": MEDIA_ROOT},
    }

STORAGES = {
    "default": default_storage,
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
