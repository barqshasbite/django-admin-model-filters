# coding=utf-8

"""Application configuration."""

from django.apps import AppConfig


class ModelFilterConfig(AppConfig):
    """Basic application configuration."""

    name = "model_filters"
    verbose_name = "Model Filters"
    default_auto_field = "django.db.models.BigAutoField"
