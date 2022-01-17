# coding=utf-8

"""Mixin tests."""

import pytest
from django.test import TestCase

from model_filters.admin.mixins import ModelFilterMixin


@pytest.mark.unit
class Tests(TestCase):
    """Mixin tests."""

    def test_init(self):
        """Setup model filter templates for proper extension."""
        mixin = ModelFilterMixin()
        self.assertEqual(
            mixin.extend_change_list_template,
            ModelFilterMixin.default_change_list_template,
        )
        self.assertEqual(
            mixin.change_list_template,
            ModelFilterMixin.model_filter_change_list_template,
        )

        mixin.change_list_template = "test template"
        mixin._setup_change_list_template()
        self.assertEqual(mixin.extend_change_list_template, "test template")
        self.assertEqual(
            mixin.change_list_template,
            ModelFilterMixin.model_filter_change_list_template,
        )
