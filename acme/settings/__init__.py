# coding=utf-8

"""Cascading settings."""

from acme.settings.base import *


if TESTING:
    print("Using testing settings.")
    from acme.settings.test import *
else:
    print("Using local settings.")
    try:
        from acme.settings.local_settings import *
    except ImportError as exc:
        exc.args = tuple(
            [f"{exc.args[0]} (Did you create a settings/local_settings.py?)"]
        )
        raise exc
