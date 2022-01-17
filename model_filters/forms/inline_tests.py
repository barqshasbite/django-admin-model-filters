# coding=utf-8

"""Field filter inline formset tests."""

from unittest import TestCase

import pytest
from django import forms

from model_filters.constants import OR_SEPARATOR
from model_filters.forms.inline import FieldFilterInlineFormset


@pytest.mark.unit
class Tests(TestCase):
    """Field filter inline formset tests."""

    def test_clean_field_filters(self):
        """Valid field filter formset data should pass."""
        self.assertIsNone(
            FieldFilterInlineFormset.clean_field_filters(
                [
                    {"field": "name"},
                    {"DELETE": True},
                ]
            )
        )
        self.assertIsNone(
            FieldFilterInlineFormset.clean_field_filters(
                [
                    {"field": "name"},
                    {"DELETE": True},
                    {"field": "description"},
                ]
            )
        )
        self.assertIsNone(
            FieldFilterInlineFormset.clean_field_filters(
                [
                    {"field": "name"},
                    {"DELETE": True},
                    {"field": OR_SEPARATOR, "DELETE": True},
                    {"field": OR_SEPARATOR},
                    {"field": "description"},
                    {"DELETE": True},
                ]
            )
        )

    def test_clean_field_filters_errors(self):
        """Invalid field filter formset data should be caught."""
        with self.assertRaises(forms.ValidationError):
            FieldFilterInlineFormset.clean_field_filters([])
        with self.assertRaises(forms.ValidationError):
            FieldFilterInlineFormset.clean_field_filters([{"DELETE": True}])
        with self.assertRaises(forms.ValidationError):
            FieldFilterInlineFormset.clean_field_filters([{"field": OR_SEPARATOR}])
        with self.assertRaises(forms.ValidationError):
            FieldFilterInlineFormset.clean_field_filters(
                [
                    {"field": OR_SEPARATOR},
                    {"field": "name"},
                ]
            )
        with self.assertRaises(forms.ValidationError):
            FieldFilterInlineFormset.clean_field_filters(
                [
                    {"field": "name"},
                    {"field": OR_SEPARATOR},
                ]
            )
        with self.assertRaises(forms.ValidationError):
            FieldFilterInlineFormset.clean_field_filters(
                [
                    {"field": "name"},
                    {"field": OR_SEPARATOR},
                    {"field": OR_SEPARATOR},
                    {"field": "description"},
                ]
            )
        with self.assertRaises(forms.ValidationError):
            FieldFilterInlineFormset.clean_field_filters(
                [
                    {"DELETE": True},
                    {"field": "name"},
                    {"DELETE": True},
                    {"field": OR_SEPARATOR},
                    {"DELETE": True},
                    {"field": OR_SEPARATOR},
                    {"DELETE": True},
                    {"field": "description"},
                    {"DELETE": True},
                ]
            )
