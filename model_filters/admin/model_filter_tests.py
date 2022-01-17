# coding=utf-8

"""Model filter admin tests."""

from unittest.mock import Mock

import pytest
from django.test import TestCase

from model_filters.admin.model_filter import ModelFilterAdminBase


@pytest.mark.functional
class Tests(TestCase):
    """Model filter manager tests."""

    def test_init(self):
        """Setup model filter templates for proper extension."""
        admin = ModelFilterAdminBase(Mock(), Mock())
        self.assertEqual(
            admin.extend_change_form_template,
            ModelFilterAdminBase.default_change_form_template,
        )
        self.assertEqual(
            admin.change_form_template,
            ModelFilterAdminBase.model_filter_change_form_template,
        )

        admin.change_form_template = "test template"
        admin._setup_change_form_template()
        self.assertEqual(admin.extend_change_form_template, "test template")
        self.assertEqual(
            admin.change_form_template,
            ModelFilterAdminBase.model_filter_change_form_template,
        )
