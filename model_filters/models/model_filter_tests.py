# coding=utf-8

"""Model filter model tests."""

from unittest import TestCase

import pytest
from django.utils import timezone
from django.utils.timezone import localtime

from model_filters.constants import DATETIME_FORMAT
from model_filters.models import ModelFilter


@pytest.mark.unit
class Tests(TestCase):
    """Model filter model tests."""

    def test_str(self):
        """Model filter to string should generate properly."""
        now = timezone.now()
        name = "Test Filter"
        self.assertEqual(
            name,
            str(ModelFilter(name=name, created=now)),
        )
        self.assertEqual(
            localtime(now).strftime(DATETIME_FORMAT),
            str(ModelFilter(created=now)),
        )
