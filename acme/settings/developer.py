# coding=utf-8

"""Developer template for creating your own `local_settings.py` file."""

# pylint: disable=wildcard-import,unused-wildcard-import

from acme.settings.base import *


# Log level for database backends. Use DEBUG to see queries.
LOGGING["loggers"]["django.db.backends"]["level"] = "INFO"

# Enable Grappelli Admin Interface
# INSTALLED_APPS.insert(0, "grappelli")

# Model Filters
MODEL_FILTERS_VIEW_OWNER_ONLY = True
MODEL_FILTERS_CHANGE_OWNER_ONLY = True
MODEL_FILTERS_DELETE_OWNER_ONLY = True
MODEL_FILTERS_ORDER_BY = None
MODEL_FILTERS_USE_GUARDIAN = False

if MODEL_FILTERS_USE_GUARDIAN:
    AUTHENTICATION_BACKENDS.append("guardian.backends.ObjectPermissionBackend")
