# coding=utf-8

"""Basic permissions test cases."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.test import TestCase, modify_settings, override_settings
from guardian.shortcuts import assign_perm

from acme.core.models import Customer
from acme.tests import new_user
from model_filters.models import ModelFilter


@pytest.mark.permissions
class Tests(TestCase):
    """Permissions tests."""

    def test_object_level_permissions(self):
        """Sanity check class and object level permissions using 'has_perm'.

        This does not test any `model_filter` code. It is just used to ensure
        class and object level permissions are behaving as expected, and as a
        reference point.
        """
        with override_settings(
            AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"]
        ):
            owner1 = new_user(is_staff=True)
            owner2 = new_user(is_staff=True)
            content_type = ContentType.objects.get_for_model(Customer)
            model_filter_1 = ModelFilter.objects.create(
                name="Test Filter 1", content_type=content_type, owner=owner1
            )
            model_filter_2 = ModelFilter.objects.create(
                name="Test Filter 2", content_type=content_type, owner=owner2
            )

            # Starts out with no class or object permissions at all.
            self.assertFalse(owner1.has_perm("model_filters.view_modelfilter"))
            self.assertFalse(owner2.has_perm("model_filters.view_modelfilter"))
            self.assertFalse(owner1.has_perm("view_modelfilter", model_filter_1))
            self.assertFalse(owner1.has_perm("view_modelfilter", model_filter_2))
            self.assertFalse(owner2.has_perm("view_modelfilter", model_filter_1))
            self.assertFalse(owner2.has_perm("view_modelfilter", model_filter_2))

            # Add "view" class permissions.
            permission = Permission.objects.get(
                content_type=ContentType.objects.get_for_model(ModelFilter),
                codename="view_modelfilter",
            )
            owner1.user_permissions.add(permission)
            owner2.user_permissions.add(permission)

            # Refresh users to avoid cached permissions.
            owner1 = get_object_or_404(get_user_model(), pk=owner1.id)
            owner2 = get_object_or_404(get_user_model(), pk=owner2.id)

            # Can now view at the class level.
            self.assertTrue(owner1.has_perm("model_filters.view_modelfilter"))
            self.assertTrue(owner2.has_perm("model_filters.view_modelfilter"))

            # Object level permissions default to False for `ModelBackend`.
            self.assertFalse(owner1.has_perm("view_modelfilter", model_filter_1))
            self.assertFalse(owner1.has_perm("view_modelfilter", model_filter_2))
            self.assertFalse(owner2.has_perm("view_modelfilter", model_filter_1))
            self.assertFalse(owner2.has_perm("view_modelfilter", model_filter_2))

            # Enable Django Guardian object level permissions backend.
            with modify_settings(
                AUTHENTICATION_BACKENDS={
                    "append": ["guardian.backends.ObjectPermissionBackend"]
                }
            ):
                # Refresh users to avoid cached permissions.
                owner1 = get_object_or_404(get_user_model(), pk=owner1.id)
                owner2 = get_object_or_404(get_user_model(), pk=owner2.id)

                # Object level permissions still false.
                self.assertFalse(owner1.has_perm("view_modelfilter", model_filter_1))
                self.assertFalse(owner1.has_perm("view_modelfilter", model_filter_2))
                self.assertFalse(owner2.has_perm("view_modelfilter", model_filter_1))
                self.assertFalse(owner2.has_perm("view_modelfilter", model_filter_2))

                # Grant "view" access to some objects.
                assign_perm("view_modelfilter", owner1, model_filter_1)
                assign_perm("view_modelfilter", owner2, model_filter_2)

                # Refresh users to avoid cached permissions.
                owner1 = get_object_or_404(get_user_model(), pk=owner1.id)
                owner2 = get_object_or_404(get_user_model(), pk=owner2.id)

                # Users now have "view" access to some objects.
                self.assertTrue(owner1.has_perm("view_modelfilter", model_filter_1))
                self.assertFalse(owner1.has_perm("view_modelfilter", model_filter_2))
                self.assertFalse(owner2.has_perm("view_modelfilter", model_filter_1))
                self.assertTrue(owner2.has_perm("view_modelfilter", model_filter_2))

                # Grant more "view" access at the object level.
                assign_perm("view_modelfilter", owner1, model_filter_2)
                assign_perm("view_modelfilter", owner2, model_filter_1)

                # Refresh users to avoid cached permissions.
                owner1 = get_object_or_404(get_user_model(), pk=owner1.id)
                owner2 = get_object_or_404(get_user_model(), pk=owner2.id)

                # Users now have "view" access to all objects.
                self.assertTrue(owner1.has_perm("view_modelfilter", model_filter_1))
                self.assertTrue(owner1.has_perm("view_modelfilter", model_filter_2))
                self.assertTrue(owner2.has_perm("view_modelfilter", model_filter_1))
                self.assertTrue(owner2.has_perm("view_modelfilter", model_filter_2))
