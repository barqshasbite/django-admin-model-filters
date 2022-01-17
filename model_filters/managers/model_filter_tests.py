# coding=utf-8

"""Model filter manager tests."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.test import TestCase, modify_settings, override_settings
from guardian.shortcuts import assign_perm

from acme.core.models import Product
from acme.tests import new_user
from model_filters.models import FieldFilter, ModelFilter


@pytest.mark.functional
class Tests(TestCase):
    """Model filter manager tests."""

    def test_with_related(self):
        """Related fields are fetched for a model filter."""
        owner = new_user(is_staff=True)
        content_type = ContentType.objects.get_for_model(Product)
        model_filter = ModelFilter.objects.create(
            name="Test Filter",
            content_type=content_type,
            owner=owner,
        )
        field_filter = FieldFilter.objects.create(
            model_filter=model_filter,
            field="name",
            operator="exact",
            value="Tornado Seeds",
            negate=False,
        )
        with self.assertNumQueries(0):
            model_filters = ModelFilter.objects.with_related()
        with self.assertNumQueries(2):
            # One query to fetch the model filters, another to prefetch `fields`.
            self.assertEqual(1, len(model_filters))
        self.assertEqual(model_filter, model_filters[0])
        with self.assertNumQueries(0):
            # No extra query when accessing `fields`.
            self.assertEqual(field_filter, model_filters[0].fields.all()[0])
            # No extra queries when accessing foreign keys.
            self.assertEqual(content_type, model_filters[0].content_type)
            self.assertEqual(owner, model_filters[0].owner)

    @pytest.mark.permissions
    def test_for_user(self):
        """All model filters a user can access are returned."""
        staff = new_user(is_staff=True)
        owner = new_user(is_staff=True)
        content_type = ContentType.objects.get_for_model(Product)
        model_filter = ModelFilter.objects.create(
            name="Test Filter",
            content_type=content_type,
            owner=owner,
        )
        # Staff cannot see any model filters.
        model_filters = ModelFilter.objects.for_user(staff)
        self.assertEqual(0, len(model_filters))

        # Owner can see their model filters.
        model_filters = ModelFilter.objects.for_user(owner)
        self.assertEqual(1, len(model_filters))
        self.assertEqual(model_filter, model_filters[0])

        with override_settings(MODEL_FILTERS_VIEW_OWNER_ONLY=False):
            # Staff without class permissions can't see the other staff model filters.
            model_filters = ModelFilter.objects.for_user(staff)
            self.assertEqual(0, len(model_filters))

            # Add class permissions.
            permission = Permission.objects.get(
                content_type=ContentType.objects.get_for_model(ModelFilter),
                codename="view_modelfilter",
            )
            staff.user_permissions.add(permission)
            staff = get_object_or_404(get_user_model(), pk=staff.id)

            # Staff with class permissions can see the other staff model filters.
            model_filters = ModelFilter.objects.for_user(staff)
            self.assertEqual(1, len(model_filters))
            self.assertEqual(model_filter, model_filters[0])

            with modify_settings(
                AUTHENTICATION_BACKENDS={
                    "append": ["guardian.backends.ObjectPermissionBackend"]
                }
            ):
                with override_settings(MODEL_FILTERS_USE_GUARDIAN=True):
                    # Staff with class permissions can still see model filters.
                    staff = get_object_or_404(get_user_model(), pk=staff.id)
                    model_filters = ModelFilter.objects.for_user(staff)
                    self.assertEqual(1, len(model_filters))

                    # Remove class level permissions to test object level.
                    staff.user_permissions.remove(permission)
                    staff = get_object_or_404(get_user_model(), pk=staff.id)

                    # Staff user no longer has access to model filters.
                    model_filters = ModelFilter.objects.for_user(staff)
                    self.assertEqual(0, len(model_filters))

                    # Give staff object level permissions to model filter.
                    assign_perm("view_modelfilter", staff, model_filter)
                    staff = get_object_or_404(get_user_model(), pk=staff.id)

                    # Staff user can see model filter again.
                    model_filters = ModelFilter.objects.for_user(staff)
                    self.assertEqual(1, len(model_filters))
                    self.assertEqual(model_filter, model_filters[0])
