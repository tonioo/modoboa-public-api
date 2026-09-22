"""Minimal settings to run the test suite without the host project.

The real settings live in modoboa-org-api. Only what the apps under test
need is defined here:

    django-admin test --pythonpath=. --settings=test_settings

SQLite and a memory cache are used unless POSTGRES_HOST and REDIS_URL are
set (production runs PostgreSQL and Redis).
"""

import os

SECRET_KEY = "not-a-secret"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "modoboa_public_api",
]

if os.environ.get("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "NAME": os.environ.get("POSTGRES_DB", "modoboa_api"),
            "USER": os.environ.get("POSTGRES_USER", "modoboa_api"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Throttling counters live in the cache.
if os.environ.get("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ["REDIS_URL"],
        }
    }

# Existing migrations use AutoField.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

ROOT_URLCONF = "modoboa_public_api.urls"

USE_TZ = True

# Read from the host project, see CLAUDE.md.
MODOBOA_CURRENT_VERSION = ("2.4.0", "https://example.test/changelog")
