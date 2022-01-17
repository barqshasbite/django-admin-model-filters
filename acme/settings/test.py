# coding=utf-8

"""Testing settings."""


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Model Filters
MODEL_FILTERS_VIEW_OWNER_ONLY = True
MODEL_FILTERS_CHANGE_OWNER_ONLY = True
MODEL_FILTERS_DELETE_OWNER_ONLY = True
MODEL_FILTERS_ORDER_BY = None
MODEL_FILTERS_USE_GUARDIAN = False
