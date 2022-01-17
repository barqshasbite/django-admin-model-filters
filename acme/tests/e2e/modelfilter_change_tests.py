# coding=utf-8

"""Model filter change tests."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.test import TestCase, override_settings
from django.urls import reverse

from acme.core.models import Customer
from acme.tests import new_user
from model_filters.constants import FILTER_PARAMETER_NAME, FORM_SAVE_APPLY, OR_SEPARATOR
from model_filters.models import FieldFilter, ModelFilter


@pytest.mark.e2e
@pytest.mark.change
class Tests(TestCase):
    """Do end-to-end change tests."""

    @pytest.mark.permissions
    def test_change_model_filter_permissions(self):
        """Basic change permissions checks for anon, user, and staff."""
        owner = new_user(is_staff=True)
        content_type = ContentType.objects.get_for_model(Customer)
        model_filter_ct = ContentType.objects.get_for_model(ModelFilter)
        permission = Permission.objects.get(
            content_type=content_type, codename="view_customer"
        )
        owner.user_permissions.add(permission)
        model_filter = ModelFilter.objects.create(
            name="Customer Filter",
            content_type=content_type,
            owner=owner,
        )
        url = reverse("admin:model_filters_modelfilter_change", args=(model_filter.id,))

        # Anonymous user should be asked to login to admin site.
        response = self.client.get(url, follow=True)
        self.assertEqual("/admin/login/", response.request["PATH_INFO"])

        # Regular user should be asked to login to admin site.
        user = new_user()
        self.client.force_login(user)
        response = self.client.get(url, follow=True)
        self.assertEqual("/admin/login/", response.request["PATH_INFO"])

        # Staff user can't access the model filter's content type, is redirected.
        staff = new_user(is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(url)
        self.assertRedirects(response, "/admin/")

        # Give staff user access to the model filter's content type.
        permission = Permission.objects.get(
            content_type=content_type, codename="change_customer"
        )
        staff.user_permissions.add(permission)

        # A staff user that does not own the model filter should still be blocked.
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/admin/")

        # Disable owner-only permissions so regular staff can get results.
        with override_settings(
            MODEL_FILTERS_VIEW_OWNER_ONLY=False, MODEL_FILTERS_CHANGE_OWNER_ONLY=False
        ):
            # Add view class permissions.
            permission = Permission.objects.get(
                content_type=model_filter_ct, codename="view_modelfilter"
            )
            staff.user_permissions.add(permission)
            staff = get_object_or_404(get_user_model(), pk=staff.id)

            # Regular staff can view, but not change.
            response = self.client.get(url, follow=True)
            self.assertEqual(200, response.status_code)
            print(response.content)
            self.assertNotContains(response, "Save")
            self.assertNotContains(response, "Delete")
            self.assertEqual(url, response.request["PATH_INFO"])

            # Give staff user access to the model filter content type.
            permission = Permission.objects.get(
                content_type=model_filter_ct, codename="change_modelfilter"
            )
            staff.user_permissions.add(permission)

            # Regular staff has permissions, access is allowed.
            response = self.client.get(url, follow=True)
            self.assertEqual(200, response.status_code)
            self.assertEqual(url, response.request["PATH_INFO"])

            # The owner of the model filter should still be allowed to change it.
            self.client.force_login(owner)
            response = self.client.get(url)
            self.assertEqual(200, response.status_code)

        # The owner of the model filter should be allowed to change it.
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_change_model_filter(self):
        """Change simple model filters and save them differently."""
        owner = new_user(is_staff=True, is_superuser=True)
        content_type = ContentType.objects.get_for_model(Customer)
        model_filter = ModelFilter.objects.create(
            name="Customer Filter",
            content_type=content_type,
            owner=owner,
        )
        field_filter = FieldFilter.objects.create(
            model_filter=model_filter,
            field="name",
            operator="exact",
            value="Wile E. Coyote",
        )
        self.client.force_login(owner)
        url = reverse("admin:model_filters_modelfilter_change", args=(model_filter.id,))
        methods = ["_save", "_continue", FORM_SAVE_APPLY]
        for submit in methods:
            data = {
                "id": model_filter.id,
                "name": "New Name",
                "description": "Fancy words.",
                "content_type": model_filter.content_type_id,
                "owner": owner.id,
                "fields-TOTAL_FORMS": 1,
                "fields-INITIAL_FORMS": 1,
                "fields-MIN_NUM_FORMS": 0,
                "fields-MAX_NUM_FORMS": 1000,
                "fields-0-id": field_filter.id,
                "fields-0-field": field_filter.field,
                "fields-0-operator": field_filter.operator,
                "fields-0-value": field_filter.value,
                submit: "Save button",
            }
            response = self.client.post(url, data=data, follow=True)
            request = response.request
            self.assertEqual(200, response.status_code)
            self.assertFalse(response.context.get("errors"))

            # The model filter should be updated.
            model_filters = ModelFilter.objects.all()
            model_filter2 = model_filters[0]
            self.assertEqual(model_filter2.name, "New Name")
            self.assertEqual(model_filter2.description, "Fancy words.")
            self.assertEqual(model_filter2.content_type, model_filter.content_type)
            self.assertEqual(model_filter2.owner, model_filter.owner)
            self.assertEqual(model_filter2.ephemeral, model_filter.ephemeral)
            self.assertEqual(1, model_filter2.fields.count())
            field_filter2 = model_filter2.fields.all()[0]
            self.assertEqual(field_filter2.field, field_filter.field)
            self.assertEqual(field_filter2.operator, field_filter.operator)
            self.assertEqual(field_filter2.value, field_filter.value)
            self.assertEqual(field_filter2.negate, field_filter.negate)

            if submit == "_save":
                # Input "_save" redirects to model filter list.
                self.assertEqual(
                    reverse("admin:model_filters_modelfilter_changelist"),
                    request["PATH_INFO"],
                )
            elif submit == "_continue":
                # Input "_continue" redirects to model filter change form.
                self.assertEqual(
                    reverse(
                        "admin:model_filters_modelfilter_change",
                        args=(model_filter.id,),
                    ),
                    request["PATH_INFO"],
                )
            elif submit == FORM_SAVE_APPLY:
                # Input "_saveapply" redirects to model filter content type list.
                filter_url = reverse(
                    f"admin:{content_type.app_label}_{content_type.model}_changelist"
                )
                self.assertEqual(
                    f"{filter_url}?{FILTER_PARAMETER_NAME}={model_filter.id}",
                    f"{request['PATH_INFO']}?{request['QUERY_STRING']}",
                )

    def test_change_model_filter_remove_field(self):
        """Remove field filters from a model filter."""
        owner = new_user(is_staff=True, is_superuser=True)
        content_type = ContentType.objects.get_for_model(Customer)
        model_filter = ModelFilter.objects.create(
            name="Customer Filter",
            content_type=content_type,
            owner=owner,
        )
        field_filter = FieldFilter.objects.create(
            model_filter=model_filter,
            field="name",
            operator="exact",
            value="Wile E. Coyote",
        )
        self.client.force_login(owner)
        url = reverse("admin:model_filters_modelfilter_change", args=(model_filter.id,))
        data = {
            "id": model_filter.id,
            "name": model_filter.name or "",
            "description": model_filter.description or "",
            "content_type": model_filter.content_type_id,
            "owner": owner.id,
            "fields-TOTAL_FORMS": 0,
            "fields-INITIAL_FORMS": 1,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
            "fields-0-id": field_filter.id,
            "fields-0-field": field_filter.field,
            "fields-0-operator": field_filter.operator,
            "fields-0-value": field_filter.value,
            "fields-0-DELETE": "checked",
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        errors = response.context.get("errors")
        self.assertTrue(errors)
        self.assertEqual("At least one field filter is required.", errors[0])

        # Add two more field filters (an OR and a valid field).
        field_filter2 = FieldFilter.objects.create(
            model_filter=model_filter,
            field=OR_SEPARATOR,
            operator="exact",
            value="",
        )
        field_filter3 = FieldFilter.objects.create(
            model_filter=model_filter,
            field="membership",
            operator="equals",
            value=Customer.MEMBERSHIP_PLATINUM,
        )

        # Try to delete the first field filter.
        data = {
            "id": model_filter.id,
            "name": model_filter.name or "",
            "description": model_filter.description or "",
            "content_type": model_filter.content_type_id,
            "owner": owner.id,
            "fields-TOTAL_FORMS": 2,
            "fields-INITIAL_FORMS": 3,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
            "fields-0-id": field_filter.id,
            "fields-0-field": field_filter.field,
            "fields-0-operator": field_filter.operator,
            "fields-0-value": field_filter.value,
            "fields-0-DELETE": "checked",
            "fields-1-id": field_filter2.id,
            "fields-1-field": field_filter2.field,
            "fields-1-operator": field_filter2.operator,
            "fields-1-value": field_filter2.value,
            "fields-2-id": field_filter3.id,
            "fields-2-field": field_filter3.field,
            "fields-2-operator": field_filter3.operator,
            "fields-2-value": field_filter3.value,
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        errors = response.context.get("errors")
        self.assertTrue(errors)
        self.assertEqual("First field filter cannot be an OR separator.", errors[0])

        # Try to delete the last field filter.
        data = {
            "id": model_filter.id,
            "name": model_filter.name or "",
            "description": model_filter.description or "",
            "content_type": model_filter.content_type_id,
            "owner": owner.id,
            "fields-TOTAL_FORMS": 2,
            "fields-INITIAL_FORMS": 3,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
            "fields-0-id": field_filter.id,
            "fields-0-field": field_filter.field,
            "fields-0-operator": field_filter.operator,
            "fields-0-value": field_filter.value,
            "fields-1-id": field_filter2.id,
            "fields-1-field": field_filter2.field,
            "fields-1-operator": field_filter2.operator,
            "fields-1-value": field_filter2.value,
            "fields-2-id": field_filter3.id,
            "fields-2-field": field_filter3.field,
            "fields-2-operator": field_filter3.operator,
            "fields-2-value": field_filter3.value,
            "fields-2-DELETE": "checked",
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        errors = response.context.get("errors")
        self.assertTrue(errors)
        self.assertEqual("Last field filter cannot be an OR separator.", errors[0])

        # Delete the middle (OR) field filter.
        data = {
            "id": model_filter.id,
            "name": model_filter.name or "",
            "description": model_filter.description or "",
            "content_type": model_filter.content_type_id,
            "owner": owner.id,
            "fields-TOTAL_FORMS": 2,
            "fields-INITIAL_FORMS": 3,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
            "fields-0-id": field_filter.id,
            "fields-0-field": field_filter.field,
            "fields-0-operator": field_filter.operator,
            "fields-0-value": field_filter.value,
            "fields-1-id": field_filter2.id,
            "fields-1-field": field_filter2.field,
            "fields-1-operator": field_filter2.operator,
            "fields-1-value": field_filter2.value,
            "fields-1-DELETE": "checked",
            "fields-2-id": field_filter3.id,
            "fields-2-field": field_filter3.field,
            "fields-2-operator": field_filter3.operator,
            "fields-2-value": field_filter3.value,
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertFalse(response.context.get("errors"))
        self.assertEqual(2, model_filter.fields.count())

    def test_change_model_filter_related_fields(self):
        """Cannot change unchangeable related fields."""
        owner = new_user(is_staff=True, is_superuser=True)
        content_type = ContentType.objects.get_for_model(Customer)
        model_filter = ModelFilter.objects.create(
            name="Customer Filter",
            content_type=content_type,
            owner=owner,
        )
        field_filter = FieldFilter.objects.create(
            model_filter=model_filter,
            field="name",
            operator="exact",
            value="Wile E. Coyote",
        )
        self.client.force_login(owner)
        url = reverse("admin:model_filters_modelfilter_change", args=(model_filter.id,))
        bad_choice = (
            "Select a valid choice. That choice is not one of the available choices."
        )

        # Try to change the owner.
        bad_data = {
            "id": model_filter.id,
            "name": model_filter.name or "",
            "description": model_filter.description or "",
            "content_type": model_filter.content_type_id,
            "owner": 9999,
            "fields-TOTAL_FORMS": 0,
            "fields-INITIAL_FORMS": 1,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
            "fields-0-id": field_filter.id,
            "fields-0-field": field_filter.field,
            "fields-0-operator": field_filter.operator,
            "fields-0-value": field_filter.value,
        }

        # Try to change the content type.
        bad_data2 = dict(bad_data)
        bad_data2["owner"] = owner.id
        bad_data2["content_type"] = 9999

        for data in [bad_data, bad_data2]:
            response = self.client.post(url, data=data, follow=True)
            self.assertEqual(200, response.status_code)
            errors = response.context.get("errors")
            self.assertTrue(errors)
            self.assertEqual(bad_choice, errors[0][0])
