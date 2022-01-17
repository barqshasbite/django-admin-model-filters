# coding=utf-8

"""List filter test cases."""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse

from acme.core.models import Customer
from acme.tests import new_user
from model_filters.constants import FILTER_PARAMETER_NAME
from model_filters.models import FieldFilter, ModelFilter


@pytest.mark.e2e
@pytest.mark.filter
class Tests(TestCase):
    """List filter tests."""

    def test_filtering_model_filter(self):
        """List filter on a ModelAdmin should work."""
        owner = new_user(is_staff=True, is_superuser=True)
        self.client.force_login(owner)
        customer1 = Customer.objects.create(
            name="Wile E. Coyote", membership=Customer.MEMBERSHIP_PLATINUM
        )
        customer2 = Customer.objects.create(
            name="Road Runner", membership=Customer.MEMBERSHIP_GOLD
        )
        content_type = ContentType.objects.get_for_model(Customer)
        model_filter = ModelFilter.objects.create(
            name="Test Filter", content_type=content_type, owner=owner
        )
        field_filter = FieldFilter.objects.create(
            model_filter=model_filter,
            field="name",
            operator="exact",
            value="Wile E. Coyote",
        )

        # Naked list.
        list_url = reverse(
            f"admin:{content_type.app_label}_{content_type.model}_changelist"
        )
        response = self.client.get(list_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(list_url, f"{response.request['PATH_INFO']}")
        self.assertEqual(response.context["cl"].result_count, 2)
        self.assertEqual(response.context["cl"].result_list[0], customer2)
        self.assertEqual(response.context["cl"].result_list[1], customer1)

        # Model filter applied.
        filter_url = f"{list_url}?{FILTER_PARAMETER_NAME}={model_filter.id}"

        # These will match the customer name.
        operators = ["", "iexact", "regex", "iregex", "contains", "icontains"]
        for operator in operators:
            if operator:
                field_filter.operator = operator
                field_filter.save()
            response = self.client.get(filter_url)
            self.assertEqual(200, response.status_code)
            self.assertEqual(
                filter_url,
                f"{response.request['PATH_INFO']}?{response.request['QUERY_STRING']}",
            )
            self.assertEqual(response.context["cl"].result_count, 1)

        # These will not match the customer name.
        operators = ["isnull", "isempty"]
        for operator in operators:
            field_filter.operator = operator
            field_filter.save()
            response = self.client.get(filter_url)
            self.assertEqual(200, response.status_code)
            self.assertEqual(
                filter_url,
                f"{response.request['PATH_INFO']}?{response.request['QUERY_STRING']}",
            )
            self.assertEqual(response.context["cl"].result_count, 0)

        # Missing filter shows naked list.
        filter_url = f"{list_url}?{FILTER_PARAMETER_NAME}=1000"
        response = self.client.get(filter_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.context["cl"].result_count, 2)
        self.assertEqual(response.context["cl"].result_list[0], customer2)
        self.assertEqual(response.context["cl"].result_list[1], customer1)

    def test_filter_menu_display(self):
        """Filter menu should show list of model filters."""
        owner1 = new_user(is_staff=True)
        owner2 = new_user(is_staff=True)
        content_type = ContentType.objects.get_for_model(Customer)
        permission = Permission.objects.get(
            content_type=content_type,
            codename="view_customer",
        )
        owner1.user_permissions.add(permission)
        owner2.user_permissions.add(permission)
        ModelFilter.objects.create(
            name="Test Filter 1", content_type=content_type, owner=owner1
        )
        model_filter_2 = ModelFilter.objects.create(
            name="Test Filter 2", content_type=content_type, owner=owner2
        )
        self.client.force_login(owner1)

        # Only the owners model filters should be in the response.
        list_url = reverse(
            f"admin:{content_type.app_label}_{content_type.model}_changelist"
        )
        response = self.client.get(list_url)
        self.assertContains(response, "Test Filter 1")
        self.assertNotContains(response, "Test Filter 2")

        # Override setting so all staff can see permissible filters.
        with override_settings(MODEL_FILTERS_VIEW_OWNER_ONLY=False):
            # Add class permissions.
            permission = Permission.objects.get(
                content_type=ContentType.objects.get_for_model(ModelFilter),
                codename="view_modelfilter",
            )
            owner1.user_permissions.add(permission)

            # The other user's model filters should be in the response with a *.
            response = self.client.get(
                f"{list_url}?{FILTER_PARAMETER_NAME}={model_filter_2.id}"
            )
            self.assertContains(response, "Test Filter 1")
            self.assertContains(response, "Test Filter 2 *")
            self.assertNotContains(response, "Edit Filter")
            self.assertEqual(response.context["choices"][0]["display"], "All")
            self.assertEqual(response.context["choices"][1]["display"], "Test Filter 1")
            self.assertEqual(
                response.context["choices"][2]["display"], "Test Filter 2 *"
            )

            # Let other staff change model filters.
            with override_settings(MODEL_FILTERS_CHANGE_OWNER_ONLY=False):
                # Still blocked since no "change" permissions.
                response = self.client.get(
                    f"{list_url}?{FILTER_PARAMETER_NAME}={model_filter_2.id}"
                )
                self.assertNotContains(response, "Edit Filter")

                # Add change permissions.
                permission = Permission.objects.get(
                    content_type=ContentType.objects.get_for_model(ModelFilter),
                    codename="change_modelfilter",
                )
                owner1.user_permissions.add(permission)

                # Can now see the edit filter link.
                response = self.client.get(
                    f"{list_url}?{FILTER_PARAMETER_NAME}={model_filter_2.id}"
                )
                self.assertContains(response, "Edit Filter")

            # Override the default ordering.
            with override_settings(MODEL_FILTERS_ORDER_BY="-created"):
                response = self.client.get(list_url)
                self.assertContains(response, "Test Filter 1")
                self.assertContains(response, "Test Filter 2 *")
                self.assertEqual(response.context["choices"][0]["display"], "All")
                self.assertEqual(
                    response.context["choices"][1]["display"], "Test Filter 2 *"
                )
                self.assertEqual(
                    response.context["choices"][2]["display"], "Test Filter 1"
                )
