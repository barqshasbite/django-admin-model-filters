# coding=utf-8

"""Model admin list filters."""

from typing import List, Tuple

from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.db.models.functions import Lower
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from model_filters.constants import (
    FILTER_PARAMETER_NAME,
    SETTING_MODEL_FILTERS_ORDER_BY,
)
from model_filters.models import ModelFilter
from model_filters.utilities import build_query_filter


class ModelFilterListFilter(admin.SimpleListFilter):
    """Allow filtering models in the changelist view using model filters."""

    title = _("Model Filters")

    parameter_name = FILTER_PARAMETER_NAME

    def __init__(self, request, params, model, model_admin):
        """Create a list filter for the request."""
        self.content_type = ContentType.objects.get_for_model(model_admin.model)
        super().__init__(request, params, model, model_admin)

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """Update the queryset with the selected model filter."""
        if not self.value():
            return queryset
        model_filter = (
            ModelFilter.objects.with_related()
            .for_user(request.user)
            .filter(id=self.value(), content_type=self.content_type)
            .first()
        )
        if model_filter:
            # Apply the model filter to the queryset. Distinct is used in
            # case duplicates arise when joining across M2M relationships.
            queryset = queryset.filter(build_query_filter(model_filter)).distinct()
            if model_filter.owner == request.user and model_filter.ephemeral:
                # Purge ephemeral model filter after first use.
                model_filter.delete()
            else:
                # Store the current model filter for later use by the
                # `ModelFilterMixin.get_changelist_instance` method.
                request.model_filter_model_filter = model_filter
            return queryset
        return queryset

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> List[Tuple[str, str]]:
        """Return valid choices for the list filter.

        Any model filters not owned by the current user are suffixed with `*`.
        """
        lookups = []
        model_filters = (
            ModelFilter.objects.for_user(request.user)
            .filter(content_type=self.content_type)
            .only("id", "name", "owner", "created")
            .order_by(*self.get_ordering())
        )
        for model_filter in model_filters:
            display = str(model_filter)
            if model_filter.owner != request.user:
                display = f"{display} *"
            lookups.append((model_filter.id, display))
        return lookups

    @staticmethod
    def get_ordering() -> List:
        """Get the arguments to pass to `order_by()` on a queryset."""
        ordering = getattr(settings, SETTING_MODEL_FILTERS_ORDER_BY, None)
        if not ordering:
            ordering = [Lower("name").asc(nulls_first=True), "-created"]
        if not isinstance(ordering, (list, tuple)):
            ordering = [ordering]
        return ordering


class OwnerListFilter(admin.SimpleListFilter):
    """Filter model filters where current user is owner."""

    title = _("owner")

    parameter_name = "owner"
    parameter_value = "me"

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """Update the queryset with the owner filter."""
        if self.value() == self.parameter_value:
            queryset = queryset.filter(owner=request.user)
        return queryset

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> List[Tuple[str, str]]:
        """Valid choices for the filter."""
        return [(self.parameter_value, _("Owned by me"))]
