# coding=utf-8

"""Model filter creation tests."""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from acme.core.models import Customer, Product
from acme.tests import new_user
from model_filters.constants import (
    FILTER_PARAMETER_NAME,
    FORM_SAVE_APPLY,
    FORM_SAVE_APPLY_DISCARD,
    OR_SEPARATOR,
)
from model_filters.models import ModelFilter


# pylint: disable=too-many-statements


@pytest.mark.e2e
@pytest.mark.create
class Tests(TestCase):
    """Do end-to-end creation tests."""

    @pytest.mark.permissions
    def test_create_model_filter_permissions(self):
        """Basic create permissions checks for anon, user, and staff."""
        url = reverse("admin:model_filters_modelfilter_add")

        # Anonymous user should be asked to login to admin site.
        response = self.client.post(url, follow=True)
        self.assertEqual("/admin/login/", response.request["PATH_INFO"])

        # Regular user should be asked to login to admin site.
        user = new_user()
        self.client.force_login(user)
        response = self.client.post(url, follow=True)
        self.assertEqual("/admin/login/", response.request["PATH_INFO"])

        # A staff user not providing a content type should be blocked.
        content_type = ContentType.objects.get_for_model(Customer)
        user = new_user(is_staff=True)
        self.client.force_login(user)
        response = self.client.post(url)
        self.assertEqual(404, response.status_code)

        # A staff user without access to the content type should be blocked.
        response = self.client.post(f"{url}?content_type={content_type.id}")
        self.assertEqual(403, response.status_code)

        # Staff user with access to the content type should be allowed to GET and POST.
        permission = Permission.objects.get(
            content_type=content_type, codename="view_customer"
        )
        user.user_permissions.add(permission)
        # GET - Form should be initialized with proper values.
        response = self.client.get(f"{url}?content_type={content_type.id}")
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            content_type.id,
            int(response.context["adminform"].form.initial["content_type"]),
        )
        self.assertEqual(
            user.id, int(response.context["adminform"].form.initial["owner"])
        )
        # POST - Form should have errors since no data was submitted.
        try:
            response = self.client.post(f"{url}?content_type={content_type.id}")
            self.assertEqual(200, response.status_code)
            self.assertTrue(response.context.get("errors"))
        except ValidationError as error:
            # Django 2 raises a validation error when missing formset data.
            self.assertIn(
                "ManagementForm data is missing or has been tampered with",
                error.messages,
            )

    def test_create_model_filter(self):
        """Create simple model filters and save them differently."""
        user = new_user(is_staff=True, is_superuser=True)
        self.client.force_login(user)

        content_type = ContentType.objects.get_for_model(Customer)
        methods = ["_save", "_continue", FORM_SAVE_APPLY, FORM_SAVE_APPLY_DISCARD]
        url = reverse("admin:model_filters_modelfilter_add")
        url = f"{url}?content_type={content_type.id}"
        for index, submit in enumerate(methods, start=0):
            data = {
                "name": f"Customer Filter {index}",
                "description": "A fancy filter.",
                "content_type": content_type.id,
                "owner": user.id,
                "fields-TOTAL_FORMS": 1,
                "fields-INITIAL_FORMS": 0,
                "fields-MIN_NUM_FORMS": 0,
                "fields-MAX_NUM_FORMS": 1000,
                "fields-0-field": "name",
                "fields-0-operator": "exact",
                "fields-0-value": "Wile E. Coyote",
                submit: "Save button",
            }
            response = self.client.post(url, data=data, follow=True)
            request = response.request
            self.assertEqual(200, response.status_code)
            self.assertFalse(response.context.get("errors"))

            model_filters = ModelFilter.objects.all()
            if submit == FORM_SAVE_APPLY_DISCARD:
                # A model filter should NOT exist when ephemeral.
                self.assertEqual(index, len(model_filters))
            else:
                # A model filter should now exist.
                self.assertEqual(index + 1, len(model_filters))
                model_filter = model_filters[index]
                self.assertEqual(model_filter.name, f"Customer Filter {index}")
                self.assertEqual(model_filter.description, "A fancy filter.")
                self.assertEqual(model_filter.content_type, content_type)
                self.assertEqual(model_filter.owner, user)
                self.assertFalse(model_filter.ephemeral)
                self.assertEqual(1, model_filter.fields.count())
                field_filter = model_filter.fields.all()[0]
                self.assertEqual(field_filter.field, "name")
                self.assertEqual(field_filter.operator, "exact")
                self.assertEqual(field_filter.value, "Wile E. Coyote")
                self.assertFalse(field_filter.negate)

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

    def test_create_model_filter_errors(self):
        """Handle errors on model filter creation."""
        self.assertEqual(0, ModelFilter.objects.count())

        user = new_user(is_staff=True, is_superuser=True)
        self.client.force_login(user)

        content_type = ContentType.objects.get_for_model(Customer)
        url = reverse("admin:model_filters_modelfilter_add")
        url = f"{url}?content_type={content_type.id}"
        data = {
            "name": "Customer Filter",
            "content_type": content_type.id,
            "owner": user.id,
            "fields-TOTAL_FORMS": 0,
            "fields-INITIAL_FORMS": 0,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
        }

        # No field filter forms.
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        context_data = response.context_data
        self.assertEqual(
            context_data["errors"][0], "At least one field filter is required."
        )

        # One field filter form, but no data.
        data.update(
            {
                "fields-TOTAL_FORMS": 1,
            }
        )
        required_error = "This field is required."

        # Missing field filter data.
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)

        # Errors found for missing field, operator, and title.
        context_data = response.context_data
        self.assertEqual(context_data["errors"][0][0], required_error)
        self.assertEqual(context_data["errors"][1][0], required_error)
        self.assertEqual(context_data["errors"][2][0], required_error)
        errors = context_data["inline_admin_formsets"][0].forms[0].errors
        self.assertIn("field", errors)
        self.assertIn(required_error, errors["field"])
        self.assertIn("operator", errors)
        self.assertIn(required_error, errors["operator"])
        self.assertIn("value", errors)
        self.assertIn(required_error, errors["value"])
        self.assertEqual(0, ModelFilter.objects.count())

        # Add invalid operator data.
        data.update(
            {
                "fields-0-field": "name",
                "fields-0-operator": "smooth",
                "fields-0-value": "Wile E. Coyote",
            }
        )
        valid_choice_error = (
            "Select a valid choice. smooth is not one of the available choices."
        )

        # Invalid field filter data.
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)

        # Errors found for invalid field filter data.
        context_data = response.context_data
        self.assertEqual(context_data["errors"][0][0], valid_choice_error)
        errors = context_data["inline_admin_formsets"][0].forms[0].errors
        self.assertIn("operator", errors)
        self.assertIn(valid_choice_error, errors["operator"])
        self.assertEqual(0, ModelFilter.objects.count())

        # Add invalid operator data for field.
        data.update(
            {
                "fields-0-field": "name",
                "fields-0-operator": "gte",
                "fields-0-value": "Wile E. Coyote",
            }
        )
        valid_choice_error = "Operator 'gte' is not allowed for this field."

        # Invalid field filter data.
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)

        # Errors found for invalid field filter data.
        context_data = response.context_data
        self.assertEqual(context_data["errors"][0][0], valid_choice_error)
        errors = context_data["inline_admin_formsets"][0].forms[0].errors
        self.assertIn("operator", errors)
        self.assertIn(valid_choice_error, errors["operator"])
        self.assertEqual(0, ModelFilter.objects.count())

        # Add invalid field data.
        data.update(
            {
                "fields-0-operator": "exact",
                "fields-0-value": "",
            }
        )
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)

        # Errors found for invalid field filter data.
        context_data = response.context_data
        self.assertEqual(context_data["errors"][0][0], required_error)
        errors = context_data["inline_admin_formsets"][0].forms[0].errors
        self.assertIn("value", errors)
        self.assertIn(required_error, errors["value"])
        self.assertEqual(0, ModelFilter.objects.count())

        # Add valid field data and ensure all is well.
        data.update(
            {
                "fields-0-value": "Wile E. Coyote",
            }
        )
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        context_data = response.context_data
        self.assertNotIn("errors", context_data)
        self.assertNotIn("inline_admin_formsets", context_data)
        self.assertEqual(1, ModelFilter.objects.count())

    def test_create_model_filter_or_validation(self):
        """Handle incorrect usage of OR separator."""
        user = new_user(is_staff=True, is_superuser=True)
        self.client.force_login(user)

        content_type = ContentType.objects.get_for_model(Customer)
        url = reverse("admin:model_filters_modelfilter_add")
        url = f"{url}?content_type={content_type.id}"

        # Starts with an OR separator.
        data = {
            "name": "Customer Filter",
            "content_type": content_type.id,
            "owner": user.id,
            "fields-TOTAL_FORMS": 1,
            "fields-INITIAL_FORMS": 0,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
            "fields-0-field": OR_SEPARATOR,
            "fields-0-operator": "exact",
            "fields-0-value": "junk",
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)

        # Errors found for using OR separator.
        context_data = response.context_data
        self.assertEqual(
            context_data["errors"][0], "First field filter cannot be an OR separator."
        )
        self.assertEqual(0, ModelFilter.objects.count())

        # Ends with an OR separator.
        data.update(
            {
                "fields-TOTAL_FORMS": 2,
                "fields-0-field": "name",
                "fields-0-operator": "exact",
                "fields-0-value": "Wile E. Coyote",
                "fields-1-field": OR_SEPARATOR,
                "fields-1-operator": "exact",
                "fields-1-value": "junk",
            }
        )
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)

        # Errors found for using OR separator.
        context_data = response.context_data
        self.assertEqual(
            context_data["errors"][0], "Last field filter cannot be an OR separator."
        )
        self.assertEqual(0, ModelFilter.objects.count())

        # Consecutive OR separators.
        data.update(
            {
                "fields-TOTAL_FORMS": 4,
                "fields-2-field": OR_SEPARATOR,
                "fields-2-operator": "exact",
                "fields-2-value": "junk",
                "fields-3-field": "name",
                "fields-3-operator": "exact",
                "fields-3-value": "Wile E. Coyote",
            }
        )
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)

        # Errors found for using OR separator.
        context_data = response.context_data
        self.assertEqual(
            context_data["errors"][0], "Cannot have consecutive OR separators."
        )
        self.assertEqual(0, ModelFilter.objects.count())

    def test_create_model_filter_value_error(self):
        """Handle errors on field filter values."""
        self.assertEqual(0, ModelFilter.objects.count())

        user = new_user(is_staff=True, is_superuser=True)
        self.client.force_login(user)

        content_type = ContentType.objects.get_for_model(Product)
        url = reverse("admin:model_filters_modelfilter_add")
        url = f"{url}?content_type={content_type.id}"

        # String for an integer value.
        data = {
            "name": "Part Filter",
            "content_type": content_type.id,
            "owner": user.id,
            "fields-TOTAL_FORMS": 1,
            "fields-INITIAL_FORMS": 0,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
            "fields-0-field": "min_age",
            "fields-0-operator": "exact",
            "fields-0-value": "5 years",
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        context_data = response.context_data
        try:
            self.assertEqual(
                context_data["errors"][0][0],
                "Value is not valid for field (PositiveSmallIntegerField): "
                "“5 years” value must be an integer.",
            )
        except AssertionError:
            # Handle slightly different messages on older Django.
            self.assertEqual(
                context_data["errors"][0][0],
                "Value is not valid for field (PositiveSmallIntegerField): "
                "'5 years' value must be an integer.",
            )

        # Junk for a datetime value.
        data.update(
            {
                "fields-0-field": "released",
                "fields-0-operator": "exact",
                "fields-0-value": "Yesterday",
            }
        )
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        context_data = response.context_data
        self.assertEqual(
            # Normalize quotes.
            context_data["errors"][0][0].replace("”", "'").replace("“", "'"),
            "Value is not valid for field (DateTimeField): "
            "'Yesterday' value has an invalid format. "
            "It must be in YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ] format.",
        )

        # Empty value for an isnull operator should be allowed.
        data = {
            "name": "Part Filter",
            "content_type": content_type.id,
            "owner": user.id,
            "fields-TOTAL_FORMS": 1,
            "fields-INITIAL_FORMS": 0,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
            "fields-0-field": "released",
            "fields-0-operator": "isnull",
            "fields-0-value": "",
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        context_data = response.context_data
        self.assertIsNone(context_data.get("errors"))
