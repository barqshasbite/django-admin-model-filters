# coding=utf-8

"""Field filter model tests."""

from unittest import TestCase

import pytest

from model_filters.models import FieldFilter


@pytest.mark.unit
class Tests(TestCase):
    """Field filter model tests."""

    def test_str(self):
        """Field filter to string should be constant."""
        self.assertEqual("Field Filter", str(FieldFilter()))
