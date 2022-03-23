# coding=utf-8

"""Model filter model."""

from django.conf import settings
from django.db import models
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from model_filters.constants import DATETIME_FORMAT
from model_filters.managers import ModelFilterQuerySet


class ModelFilter(models.Model):
    """A model filter."""

    id = models.BigAutoField(
        _("ID"),
        auto_created=True,
        primary_key=True,
        serialize=False,
    )
    name = models.CharField(
        _("name"),
        max_length=1024,
        null=True,
        blank=True,
        help_text=_("A name for the model filter."),
    )
    description = models.TextField(
        _("description"),
        null=True,
        blank=True,
        help_text=_("An optional description of the model filter."),
    )
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        verbose_name=_("content type"),
        on_delete=models.CASCADE,
        help_text=_("The model being filtered."),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("owner"),
        related_name="model_filters",
        on_delete=models.CASCADE,
        help_text=_("The user that created, and owns, the model filter."),
    )
    created = models.DateTimeField(
        _("created"),
        auto_now_add=True,
        help_text=_("The date and time the model filter was created."),
    )
    ephemeral = models.BooleanField(
        _("ephemeral"),
        default=False,
        null=False,
        blank=False,
        help_text=_("A one-off model filter that is deleted after initial use."),
    )

    objects = ModelFilterQuerySet.as_manager()

    class Meta:
        """Model configuration."""

        verbose_name = _("model filter")
        verbose_name_plural = _("model filters")
        indexes = [
            # Use `Lower("name")` when dropping Django 2.2 support.
            models.Index(fields=["name"]),
            models.Index(fields=["-created"]),
        ]

    def __str__(self) -> str:
        """Display name."""
        return self.name or localtime(self.created).strftime(DATETIME_FORMAT)
