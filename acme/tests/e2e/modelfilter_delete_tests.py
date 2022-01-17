# coding=utf-8

"""Model filter delete tests."""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse

from acme.core.models import Customer
from acme.tests import new_user
from model_filters.models import ModelFilter


@pytest.mark.e2e
@pytest.mark.delete
class Tests(TestCase):
    """Do end-to-end delete tests."""

    @pytest.mark.permissions
    def test_delete_model_filter_permissions(self):
        """Basic delete permissions checks for anon, user, and staff."""
        owner = new_user(is_staff=True)
        content_type = ContentType.objects.get_for_model(Customer)
        model_filter = ModelFilter.objects.create(
            name="Customer Filter",
            content_type=content_type,
            owner=owner,
        )
        url = reverse("admin:model_filters_modelfilter_delete", args=(model_filter.id,))

        # Anonymous user should be asked to login to admin site.
        response = self.client.post(url)
        self.assertRedirects(response, f"/admin/login/?next={url}")
        self.assertTrue(ModelFilter.objects.filter(id=model_filter.id).exists())

        # Regular user should be asked to login to admin site.
        self.client.force_login(new_user())
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, f"/admin/login/?next={url}")
        self.assertTrue(ModelFilter.objects.filter(id=model_filter.id).exists())

        # A regular staff user without permissions should be blocked.
        staff = new_user(is_staff=True)
        self.client.force_login(staff)
        response = self.client.post(url)
        self.assertRedirects(response, "/admin/")
        self.assertTrue(ModelFilter.objects.filter(id=model_filter.id).exists())

        permission = Permission.objects.get(
            content_type=content_type, codename="view_customer"
        )
        staff.user_permissions.add(permission)

        # A regular staff user with permissions should still be blocked.
        response = self.client.post(url)
        self.assertRedirects(response, "/admin/")
        self.assertTrue(ModelFilter.objects.filter(id=model_filter.id).exists())

        # With the owner-only permissions disabled, regular staff has access.
        with override_settings(
            MODEL_FILTERS_VIEW_OWNER_ONLY=False, MODEL_FILTERS_DELETE_OWNER_ONLY=False
        ):
            # Add class permissions.
            permission = Permission.objects.get(
                content_type=ContentType.objects.get_for_model(ModelFilter),
                codename="view_modelfilter",
            )
            staff.user_permissions.add(permission)

            # Regular staff is still blocked since no "delete" permissions.
            response = self.client.post(url, data=dict(post="yes"))
            self.assertEqual(403, response.status_code)
            self.assertTrue(ModelFilter.objects.filter(id=model_filter.id).exists())

            # Give staff user "delete" permission to the model filter.
            permission = Permission.objects.get(
                content_type=ContentType.objects.get_for_model(ModelFilter),
                codename="delete_modelfilter",
            )
            staff.user_permissions.add(permission)

            # Regular staff has permissions, deletion is allowed.
            response = self.client.post(url, data=dict(post="yes"))
            self.assertRedirects(
                response, reverse("admin:model_filters_modelfilter_changelist")
            )
            self.assertFalse(ModelFilter.objects.filter(id=model_filter.id).exists())

    def test_delete_own_model_filter(self):
        """Basic delete permissions checks for anon, user, and staff."""
        owner = new_user(is_staff=True)
        content_type = ContentType.objects.get_for_model(Customer)
        model_filter = ModelFilter.objects.create(
            name="Customer Filter 2",
            content_type=content_type,
            owner=owner,
        )
        url = reverse("admin:model_filters_modelfilter_delete", args=(model_filter.id,))
        self.client.force_login(owner)

        # Even an owner must have access to the content type to proceed.
        response = self.client.post(url, data=dict(post="yes"))
        self.assertEqual(403, response.status_code)
        self.assertTrue(ModelFilter.objects.filter(id=model_filter.id).exists())

        # Give owner permission to the model filter's content type.
        permission = Permission.objects.get(
            content_type=content_type, codename="view_customer"
        )
        owner.user_permissions.add(permission)

        # Owner may now delete the model filter.
        response = self.client.post(url, data=dict(post="yes"))
        self.assertRedirects(
            response, reverse("admin:model_filters_modelfilter_changelist")
        )
        self.assertFalse(ModelFilter.objects.filter(id=model_filter.id).exists())

        # Override owner-only permissions.
        with override_settings(
            MODEL_FILTERS_VIEW_OWNER_ONLY=False, MODEL_FILTERS_DELETE_OWNER_ONLY=False
        ):
            model_filter = ModelFilter.objects.create(
                name="Customer Filter",
                content_type=content_type,
                owner=owner,
            )
            url = reverse(
                "admin:model_filters_modelfilter_delete", args=(model_filter.id,)
            )
            # Owner can still delete the model filter.
            response = self.client.post(url, data=dict(post="yes"))
            self.assertRedirects(
                response, reverse("admin:model_filters_modelfilter_changelist")
            )
            self.assertFalse(ModelFilter.objects.filter(id=model_filter.id).exists())
