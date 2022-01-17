# coding=utf-8

"""Model filter queryset for user in the manager."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from model_filters.utilities import use_guardian, view_owner_only


try:
    from guardian.shortcuts import get_objects_for_user
except (ImportError, RuntimeError):
    get_objects_for_user = None


class ModelFilterQuerySet(models.QuerySet):
    """Custom model filter queryset."""

    def with_related(self):
        """Return model filters with related fields."""
        return self.select_related("content_type", "owner").prefetch_related("fields")

    def for_user(self, user: AbstractUser):
        """Only return model filters the user has explicit access to.

        Either as the direct owner, or through the permissions framework.
        """
        queryset = self.all()
        if view_owner_only():
            return queryset.filter(owner=user)
        view_permission = "view_modelfilter"
        if use_guardian() and get_objects_for_user is not None:
            base = queryset.model._default_manager.get_queryset()
            permissions = base.filter(owner=user) | get_objects_for_user(
                user, view_permission, queryset.model
            )
            queryset &= permissions
        elif not user.has_perm(f"model_filters.{view_permission}"):
            # No class level view permissions. Restrict to owned filters.
            queryset = queryset.filter(owner=user)
        return queryset
