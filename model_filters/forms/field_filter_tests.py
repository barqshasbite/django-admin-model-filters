# coding=utf-8

"""Field filter form tests."""

from collections import OrderedDict
from unittest import TestCase
from unittest.mock import Mock, patch

import pytest
from django.db import models

from model_filters.constants import OR_SEPARATOR
from model_filters.forms.field_filter import FieldFilterForm


@pytest.mark.unit
class Tests(TestCase):
    """Field filter form tests."""

    def test_init(self):
        """Field filter form should be initialized properly with no args."""
        form = FieldFilterForm()
        self.assertIsNone(form.model)
        self.assertEqual({}, form.field_operators)
        self.assertEqual({}, form.field_values)
        self.assertEqual(
            FieldFilterForm.EXTRA_FIELD_CHOICES, form.fields["field"].choices
        )

    def test_init_args(self):
        """Field filter form should be initialized properly with args."""
        model = Mock()
        field_choices = OrderedDict({"test": "Test"})
        field_operators = {"field": [{"exact": "Exact"}]}
        field_values = {"field": [{"name": "value"}]}
        form = FieldFilterForm(
            model=model,
            field_choices=field_choices,
            field_operators=field_operators,
            field_values=field_values,
        )
        self.assertEqual(model, form.model)
        self.assertEqual(
            list(field_choices.items()) + FieldFilterForm.EXTRA_FIELD_CHOICES,
            form.fields["field"].choices,
        )
        self.assertEqual(field_operators, form.field_operators)
        self.assertEqual(field_values, form.field_values)

    @patch("model_filters.forms.field_filter.FieldFilterForm._clean_value")
    @patch("model_filters.forms.field_filter.FieldFilterForm._clean_operator")
    def test_clean(self, mock_operator, mock_value):
        """Field filter values should be valid."""
        mock_operator.return_value = "cleaned operator"
        mock_value.return_value = "cleaned value"
        form = FieldFilterForm()
        form.cleaned_data = {}
        form._errors = {}
        cleaned_data = form.clean()
        self.assertTrue(mock_operator.called)
        self.assertEqual(cleaned_data["operator"], "cleaned operator")
        self.assertTrue(mock_value.called)
        self.assertEqual(cleaned_data["value"], "cleaned value")

    @patch("model_filters.forms.field_filter.get_fields_from_path")
    def test_clean_value(self, mock_get_field):
        """Field filter should have valid value field."""
        mock_get_field.return_value = [Mock(to_python=Mock())]
        form = FieldFilterForm()
        self.assertIsNone(form._clean_value({}))
        self.assertIsNone(form._clean_value({"field": ""}))
        self.assertIsNone(form._clean_value({"field": "name"}))
        self.assertIsNone(form._clean_value({"field": "name", "operator": ""}))
        self.assertIsNone(form._clean_value({"field": "name", "operator": "exact"}))
        self.assertEqual(
            "Road Runner",
            form._clean_value(
                {"field": "name", "operator": "exact", "value": "Road Runner"}
            ),
        )

    def test_clean_value_no_value(self):
        """Field filter should have valid value field for OR separator."""
        form = FieldFilterForm()
        form._errors = {"value": "no bueno"}
        self.assertEqual(
            "",
            form._clean_value(
                {"field": "explosive", "operator": OR_SEPARATOR, "value": "junk"}
            ),
        )
        self.assertFalse(form.fields["value"].required)
        self.assertEqual({}, form._errors)

        form = FieldFilterForm()
        form._errors = {"value": "no bueno"}
        self.assertEqual(
            "",
            form._clean_value(
                {"field": OR_SEPARATOR, "operator": "exact", "value": "junk"}
            ),
        )
        self.assertFalse(form.fields["value"].required)
        self.assertEqual({}, form._errors)

        form = FieldFilterForm()
        form._errors = {"value": "no bueno"}
        self.assertEqual(
            "", form._clean_value({"field": "explosive", "operator": "istrue"})
        )
        self.assertEqual({}, form._errors)

    @patch("model_filters.forms.field_filter.get_fields_from_path")
    def test_clean_value_bad_int_value(self, mock_get_field):
        """Field filter should validate bad value types."""
        mock_get_field.return_value = [models.IntegerField()]
        form = FieldFilterForm()
        form.cleaned_data = {}
        self.assertEqual(
            "Road Runner",
            form._clean_value(
                {"field": "age", "operator": "exact", "value": "Road Runner"}
            ),
        )
        try:
            self.assertEqual(
                form.errors["value"],
                [
                    "Value is not valid for field (IntegerField): "
                    "“Road Runner” value must be an integer."
                ],
            )
        except AssertionError:
            self.assertEqual(
                form.errors["value"],
                [
                    "Value is not valid for field (IntegerField): "
                    "'Road Runner' value must be an integer."
                ],
            )

    @patch("model_filters.forms.field_filter.get_fields_from_path")
    def test_clean_value_exception(self, mock_get_field):
        """Field filter should handle exceptions from bad value types."""
        mock_get_field.return_value = [
            Mock(
                to_python=Mock(side_effect=ValueError("Bad value!")),
                get_internal_type=Mock(return_value="MockField"),
            )
        ]

        form = FieldFilterForm()
        form.cleaned_data = {}
        self.assertEqual(
            "Road Runner",
            form._clean_value(
                {"field": "age", "operator": "exact", "value": "Road Runner"}
            ),
        )
        self.assertEqual(
            form.errors["value"],
            ["Value is not valid for field (MockField): Bad value!"],
        )

    def test_clean_operator(self):
        """Field filter should validate operators."""
        form = FieldFilterForm()
        form.cleaned_data = {}
        self.assertIsNone(form._clean_operator({}))
        self.assertIsNone(form._clean_operator({"field": ""}))
        self.assertIsNone(form._clean_operator({"field": "name"}))
        self.assertIsNone(form._clean_operator({"field": "name", "operator": ""}))
        self.assertEqual(
            "exact", form._clean_operator({"field": "name", "operator": "exact"})
        )
        self.assertEqual(
            form.errors["operator"], ["Operator 'exact' is not allowed for this field."]
        )

        # Valid setup.
        form = FieldFilterForm(
            field_operators={"name": [{"key": "exact", "value": "Exact"}]}
        )
        self.assertEqual(
            "exact", form._clean_operator({"field": "name", "operator": "exact"})
        )
        self.assertFalse("operator" in form.errors)

    def test_clean_operator_with_or(self):
        """Field filter should validate operators."""
        form = FieldFilterForm(
            field_operators={"name": [{"key": "exact", "value": "Exact"}]}
        )
        self.assertEqual(
            "exact", form._clean_operator({"field": OR_SEPARATOR, "operator": "exact"})
        )
        self.assertFalse("operator" in form.errors)
