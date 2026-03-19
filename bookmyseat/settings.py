from pathlib import Path
import os
import shutil
import sys
import tempfile
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

DEBUG = os.getenv("DEBUG", "False") == "True"


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _clean_env(name, default=None):
    value = os.getenv(name)
    if value is None:
        return default
    cleaned = value.strip().strip("'").strip('"')
    return cleaned or default

ALLOWED_HOSTS = [
    ".vercel.app",
    "127.0.0.1",
    "localhost"
]

# ---------------- APPS ----------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'cloudinary_storage',
    'cloudinary',

    'movies',
    'users',
]

# ---------------- MIDDLEWARE ----------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'bookmyseat.middleware.SafeAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ---------------- URLS ----------------

ROOT_URLCONF = 'bookmyseat.urls'

# ---------------- TEMPLATES ----------------

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

# ---------------- DATABASE ----------------

DATABASE_URL = _clean_env("DATABASE_URL")
DB_CONN_MAX_AGE = int(_clean_env("DB_CONN_MAX_AGE", "0"))
DB_SSL_REQUIRE = _env_flag("DB_SSL_REQUIRE", True)
RUNNING_ON_VERCEL = _env_flag("VERCEL")
LOCAL_SQLITE_COMMANDS = {
    "runserver",
    "shell",
    "check",
    "createsuperuser",
    "makemigrations",
    "migrate",
    "showmigrations",
    "test",
}
USE_SQLITE_LOCAL = os.getenv("USE_SQLITE_LOCAL")
USE_DEMO_DATABASE = os.getenv("USE_DEMO_DATABASE")
ALLOW_SQLITE_FALLBACK = _env_flag("ALLOW_SQLITE_FALLBACK", False)

if USE_SQLITE_LOCAL is None:
    USE_SQLITE_LOCAL = len(sys.argv) > 1 and sys.argv[1] in LOCAL_SQLITE_COMMANDS
else:
    USE_SQLITE_LOCAL = USE_SQLITE_LOCAL.lower() == "true"

if USE_DEMO_DATABASE is None:
    USE_DEMO_DATABASE = False
else:
    USE_DEMO_DATABASE = USE_DEMO_DATABASE.lower() == "true"

USING_SQLITE_DATABASE = USE_SQLITE_LOCAL or USE_DEMO_DATABASE
DEMO_MODE = USE_DEMO_DATABASE


def _runtime_demo_database_path():
    bundled_database = BASE_DIR / "db.sqlite3"
    if not bundled_database.exists():
        return bundled_database

    if USE_DEMO_DATABASE and RUNNING_ON_VERCEL:
        runtime_database = Path(tempfile.gettempdir()) / "bookmyseat-demo.sqlite3"
        try:
            if (
                not runtime_database.exists()
                or bundled_database.stat().st_mtime > runtime_database.stat().st_mtime
            ):
                shutil.copy2(bundled_database, runtime_database)
            return runtime_database
        except OSError:
            return bundled_database

    return bundled_database


DEMO_DATABASE_PATH = _runtime_demo_database_path()

if DATABASE_URL and not USING_SQLITE_DATABASE:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=DB_CONN_MAX_AGE,
            ssl_require=DB_SSL_REQUIRE,
        )
    }
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"].setdefault("connect_timeout", 10)
    if DB_SSL_REQUIRE:
        DATABASES["default"]["OPTIONS"].setdefault("sslmode", "require")
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DEMO_DATABASE_PATH,
        }
    }

DATABASES["sqlite_fallback"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": DEMO_DATABASE_PATH,
}

# ---------------- AUTH & LOCALE ----------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
SESSION_ENGINE = os.getenv(
    "SESSION_ENGINE",
    "django.contrib.sessions.backends.signed_cookies"
)
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

# ---------------- STATIC ----------------

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

if DEBUG or USING_SQLITE_DATABASE:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------- EMAIL ----------------

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ---------------- PAYMENT ----------------

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# ---------------- CLOUDINARY ----------------

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv("CLOUDINARY_CLOUD_NAME"),
    'API_KEY': os.getenv("CLOUDINARY_API_KEY"),
    'API_SECRET': os.getenv("CLOUDINARY_API_SECRET"),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ---------------- SECURITY ----------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
