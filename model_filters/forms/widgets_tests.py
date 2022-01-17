# coding=utf-8

"""Form widget tests."""

from unittest import TestCase

import pytest

from model_filters.forms.widgets import FieldSelect


@pytest.mark.unit
class Tests(TestCase):
    """Form widget tests."""

    def test_create_option(self):
        """Title should should be set to the value on an option."""
        field = FieldSelect()
        option = field.create_option("widget", "goober", "label", False, 0)
        self.assertEqual(option["name"], "widget")
        self.assertEqual(option["value"], "goober")
        self.assertEqual(option["selected"], False)
        self.assertEqual(option["index"], "0")
        self.assertEqual(option["attrs"]["title"], option["value"])
