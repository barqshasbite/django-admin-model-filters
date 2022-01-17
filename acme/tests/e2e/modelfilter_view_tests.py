# coding=utf-8

"""Model filter view tests."""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse

from acme.core.models import Customer
from acme.tests import new_user
from model_filters.admin.list_filters import OwnerListFilter
from model_filters.models import ModelFilter


@pytest.mark.e2e
@pytest.mark.view
class Tests(TestCase):
    """Do end-to-end view tests."""

    @pytest.mark.permissions
    def test_view_model_filter_permissions(self):
        """Basic view permissions checks for anon, user, and staff."""
        staff = new_user(is_staff=True)
        content_type = ContentType.objects.get_for_model(Customer)
        model_filter = ModelFilter.objects.create(
            name="Customer Filter",
            content_type=content_type,
            owner=staff,
        )
        url = reverse("admin:model_filters_modelfilter_changelist")
        owner_parameter_name = OwnerListFilter.parameter_name
        owner_parameter_value = OwnerListFilter.parameter_value
        owner_url = f"{url}?{owner_parameter_name}={owner_parameter_value}"

        # Anonymous user should be asked to login to admin site.
        response = self.client.get(url, follow=True)
        self.assertEqual("/admin/login/", response.request["PATH_INFO"])

        # Regular user should be asked to login to admin site.
        user = new_user()
        self.client.force_login(user)
        response = self.client.get(url, follow=True)
        self.assertEqual("/admin/login/", response.request["PATH_INFO"])

        # A regular staff user should be allowed, but not see any results.
        user = new_user(is_staff=True)
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.context["cl"].result_count, 0)

        # Disable the owner-only permissions.
        with override_settings(MODEL_FILTERS_VIEW_OWNER_ONLY=False):
            # No class level permissions.
            response = self.client.get(url)
            self.assertEqual(200, response.status_code)
            self.assertEqual(response.context["cl"].result_count, 0)

            # Add class permissions.
            permission = Permission.objects.get(
                content_type=ContentType.objects.get_for_model(ModelFilter),
                codename="view_modelfilter",
            )
            user.user_permissions.add(permission)

            # Regular staff has results.
            response = self.client.get(url)
            self.assertEqual(200, response.status_code)
            self.assertEqual(response.context["cl"].result_count, 1)
            self.assertEqual(response.context["cl"].result_list[0], model_filter)

            # Filtering by regular staff as owner should not have any results.
            response = self.client.get(owner_url)
            self.assertEqual(200, response.status_code)
            self.assertEqual(response.context["cl"].result_count, 0)

        # Owner of the model filter should see it in the list.
        for next_url in [url, owner_url]:
            self.client.force_login(staff)
            response = self.client.get(next_url)
            self.assertEqual(200, response.status_code)
            self.assertEqual(response.context["cl"].result_count, 1)
            self.assertEqual(response.context["cl"].result_list[0], model_filter)
