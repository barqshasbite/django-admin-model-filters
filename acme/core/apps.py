# coding=utf-8

"""Application configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "acme.core"
    label = "core"
