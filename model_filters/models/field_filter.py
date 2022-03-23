# coding=utf-8

"""Field filter model."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class FieldFilter(models.Model):
    """A field filter configuration for a model filter."""

    id = models.BigAutoField(
        _("ID"),
        auto_created=True,
        primary_key=True,
        serialize=False,
    )
    model_filter = models.ForeignKey(
        "model_filters.ModelFilter",
        verbose_name=_("model filter"),
        related_name="fields",
        on_delete=models.CASCADE,
        help_text=_("The model filter that the field filter belongs to."),
    )
    field = models.TextField(
        _("field"),
        help_text=_("The path to the field to filter."),
    )
    operator = models.CharField(
        _("operator"),
        max_length=1024,
        help_text=_("The operator to use for the field value."),
    )
    value = models.TextField(
        _("value"),
        help_text=_("The value to filter the field with."),
    )
    negate = models.BooleanField(
        _("negate"),
        default=False,
        help_text=_("Negate the query filter."),
    )

    class Meta:
        """Model configuration."""

        ordering = ("id",)
        verbose_name = _("field filter")
        verbose_name_plural = _("field filters")

    def __str__(self):
        """Display name."""
        return str(_("Field Filter"))
