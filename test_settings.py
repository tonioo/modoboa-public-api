"""Minimal settings to run the test suite without the host project.

The real settings live in modoboa-org-api. Only what the apps under test
need is defined here:

    django-admin test --pythonpath=. --settings=test_settings

SQLite is used unless POSTGRES_HOST is set (production runs PostgreSQL).
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

# Existing migrations use AutoField.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

ROOT_URLCONF = "modoboa_public_api.urls"

USE_TZ = True

# Read from the host project, see CLAUDE.md.
MODOBOA_CURRENT_VERSION = ("2.4.0", "https://example.test/changelog")
