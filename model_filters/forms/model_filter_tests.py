# coding=utf-8

"""Model filter form tests."""

from unittest import TestCase
from unittest.mock import Mock, patch

import pytest

from model_filters.forms.model_filter import ModelFilterForm
from model_filters.models import ModelFilter


@pytest.mark.unit
class Tests(TestCase):
    """Model filter form tests."""

    @patch("model_filters.forms.model_filter.ModelFilterForm._update_owner_choices")
    @patch(
        "model_filters.forms.model_filter.ModelFilterForm._update_content_type_choices"
    )
    def test_init(self, mock_content_choices, mock_owner_choices):
        """Form should be initialized properly."""
        form = ModelFilterForm(instance=ModelFilter())
        self.assertIsNone(form.fields["content_type"].empty_label)
        self.assertFalse(form.fields["content_type"].widget.can_add_related)
        self.assertFalse(form.fields["content_type"].widget.can_change_related)
        self.assertFalse(form.fields["content_type"].widget.can_delete_related)
        self.assertIsNone(form.fields["owner"].empty_label)
        self.assertFalse(form.fields["owner"].widget.can_add_related)
        self.assertFalse(form.fields["owner"].widget.can_change_related)
        self.assertFalse(form.fields["owner"].widget.can_delete_related)
        self.assertEqual(2, form.fields["description"].widget.attrs["rows"])
        self.assertTrue(mock_content_choices.called)
        self.assertTrue(mock_owner_choices.called)

    @patch("model_filters.forms.model_filter.ModelFilterForm._update_owner_choices")
    @patch(
        "model_filters.forms.model_filter.ModelFilterForm._update_content_type_choices"
    )
    def test_get_content_type(self, mock_content_choices, mock_owner_choices):
        """Content type should be available."""
        form = ModelFilterForm(instance=ModelFilter(pk=1, content_type_id=42))
        self.assertEqual(42, form._get_content_type())
        form = ModelFilterForm(initial={"content_type": "Hey"}, data={})
        self.assertEqual("Hey", form._get_content_type())
        form = ModelFilterForm(initial={}, data={"content_type": "Ho"})
        self.assertEqual("Ho", form._get_content_type())
        form = ModelFilterForm(initial={}, data={})
        self.assertIsNone(form._get_content_type())
        self.assertTrue(mock_content_choices.called)
        self.assertTrue(mock_owner_choices.called)

    @patch("model_filters.forms.model_filter.ModelFilterForm._update_owner_choices")
    @patch(
        "model_filters.forms.model_filter.ModelFilterForm._update_content_type_choices"
    )
    def test_get_owner(self, mock_content_choices, mock_owner_choices):
        """Owner should be available."""
        form = ModelFilterForm(instance=ModelFilter(pk=1, owner_id=42))
        self.assertEqual(42, form._get_owner())
        form = ModelFilterForm(initial={"owner": "Hey"}, data={})
        self.assertEqual("Hey", form._get_owner())
        form = ModelFilterForm(initial={}, data={"owner": "Ho"})
        self.assertEqual("Ho", form._get_owner())
        form = ModelFilterForm(initial={}, data={})
        self.assertIsNone(form._get_owner())
        self.assertTrue(mock_content_choices.called)
        self.assertTrue(mock_owner_choices.called)

    @patch("model_filters.forms.model_filter.ModelFilterForm._update_choices")
    @patch("model_filters.forms.model_filter.ModelFilterForm._get_content_type")
    @patch("model_filters.forms.model_filter.ModelFilterForm._update_owner_choices")
    def test_update_content_type_choices(
        self, mock_owner_choices, mock_content_type, mock_choices
    ):
        """Update choices for content type."""
        mock_content_type.return_value = "mock content type"
        ModelFilterForm(instance=ModelFilter(pk=1, owner_id=42))
        self.assertTrue(mock_content_type.called)
        self.assertTrue(mock_choices.called)
        self.assertTrue(mock_choices.call_args_list[0][0][0], "mock content type")
        self.assertTrue(mock_choices.call_args_list[0][0][1], "content_type")
        self.assertTrue(mock_owner_choices.called)

    @patch("model_filters.forms.model_filter.ModelFilterForm._update_choices")
    @patch("model_filters.forms.model_filter.ModelFilterForm._get_owner")
    @patch(
        "model_filters.forms.model_filter.ModelFilterForm._update_content_type_choices"
    )
    def test_update_owner_choices(self, mock_content_choices, mock_owner, mock_choices):
        """Update choices for owner."""
        mock_owner.return_value = "mock owner"
        ModelFilterForm(instance=ModelFilter(pk=1, owner_id=42))
        self.assertTrue(mock_owner.called)
        self.assertTrue(mock_choices.called)
        self.assertTrue(mock_choices.call_args_list[0][0][0], "mock owner")
        self.assertTrue(mock_choices.call_args_list[0][0][1], "owner")
        self.assertTrue(mock_content_choices.called)

    @patch("model_filters.forms.model_filter.ModelFilterForm._update_owner_choices")
    @patch(
        "model_filters.forms.model_filter.ModelFilterForm._update_content_type_choices"
    )
    def test_update_choices(self, mock_content_choices, mock_owner_choices):
        """Update choices for field."""
        form = ModelFilterForm(instance=ModelFilter(pk=1, owner_id=42))
        form._update_choices(None, "owner")
        self.assertEqual([], form.fields["owner"].choices)
        form.fields["owner"].queryset = Mock(
            all=Mock(
                return_value=Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value="mocked")))
                )
            )
        )
        form._update_choices(42, "owner")
        self.assertEqual("mocked", form.fields["owner"].queryset)
        self.assertTrue(mock_content_choices.called)
        self.assertTrue(mock_owner_choices.called)
