# coding=utf-8

"""Field filter inlines."""

from typing import Optional

from django.contrib import admin
from django.http import HttpRequest

from model_filters.forms.field_filter import FieldFilterForm
from model_filters.forms.inline import FieldFilterInlineFormset
from model_filters.models import FieldFilter, ModelFilter


class FieldFilterTabularInline(admin.TabularInline):
    """A tabular inline form for managing field filters on a model filter."""

    form = FieldFilterForm
    formset = FieldFilterInlineFormset
    model = FieldFilter
    can_delete = True

    def get_extra(self, request, obj=None, **kwargs):
        """Set the proper number of extra forms."""
        return 0 if obj else 1

    def has_add_permission(self, request, obj):
        """Determine if a user can add a field filter."""
        return self._has_permission(request)

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[ModelFilter] = None
    ) -> bool:
        """Determine if a user can view field filter inlines."""
        return self._has_permission(request)

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[ModelFilter] = None
    ) -> bool:
        """Determine if a user can change a field filter."""
        return self._has_permission(request)

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[ModelFilter] = None
    ) -> bool:
        """Determine if a user can delete a field filter."""
        return self._has_permission(request)

    @staticmethod
    def _has_permission(request: HttpRequest):
        """Determine if a user has field filter permissions.

        Managing field filters can only be done from within the model filter
        admin change view, which would have already checked if the user has
        permissions to change the model filter. So just return True for those
        that have access to the admin site.
        """
        return request.user.is_superuser or request.user.is_staff
