# coding=utf-8

"""Application utilities tests."""

from collections import OrderedDict
from unittest import TestCase
from unittest.mock import Mock, patch

import pytest
from django.db.models import BooleanField, DecimalField, Q, URLField
from django.test import modify_settings, override_settings

from model_filters import constants, utilities
from model_filters.forms.field_filter import FieldFilterForm


@pytest.mark.unit
class Tests(TestCase):
    """Utilities tests."""

    @patch("model_filters.utilities.get_fields_from_path")
    def test_get_clean_filter_fields(self, mock_get_fields):
        """Clean a list of filter fields."""
        model = Mock()
        fields = ["name", "description", ("status", "special status!")]
        mock_get_fields.side_effect = [
            [Mock(verbose_name="name")],
            [Mock(verbose_name="description")],
            [Mock(verbose_name="status")],
        ]
        cleaned = utilities.get_clean_filter_fields(model, fields, use_title_case=True)
        self.assertEqual(
            OrderedDict(
                name="Name",
                description="Description",
                status="special status!",
            ),
            cleaned,
        )
        mock_get_fields.side_effect = [
            [Mock(verbose_name="name")],
        ]
        cleaned = utilities.get_clean_filter_fields(
            model, ["name"], use_title_case=False
        )
        self.assertEqual(OrderedDict(name="name"), cleaned)

    def test_get_clean_filter_fields_errors(self):
        """Raise errors if filter fields are configured wrong."""
        with self.assertRaises(ValueError):
            utilities.get_clean_filter_fields(Mock(), [1])
        with self.assertRaises(ValueError):
            utilities.get_clean_filter_fields(Mock(), [[]])
        with self.assertRaises(ValueError):
            utilities.get_clean_filter_fields(Mock(), [[1, "1"]])
        with self.assertRaises(ValueError):
            utilities.get_clean_filter_fields(Mock(), [["1", 1]])

    @patch("model_filters.utilities.get_fields_from_path")
    def test_get_field_operators(self, mock_get_fields):
        """Get operators for a field."""
        model = Mock()
        field_paths = ["mock", "char", "bool", "numeric"]
        get_fields_side_effect = [
            [Mock()],  # no match, use defaults
            [URLField()],  # extends CharField
            [BooleanField()],
            [DecimalField()],
        ]
        mock_get_fields.side_effect = get_fields_side_effect
        query_form = FieldFilterForm
        operators = utilities.get_field_operators(model, field_paths, query_form)
        self.assertEqual(
            {
                "mock": [
                    {"key": "exact", "display": "Equals (exact)"},
                    {"key": "isnull", "display": "Is NULL"},
                ],
                "char": [
                    {"key": "exact", "display": "Equals (case-sensitive)"},
                    {"key": "iexact", "display": "Equals (ignore case)"},
                    {"key": "contains", "display": "Contains (case-sensitive)"},
                    {"key": "icontains", "display": "Contains (ignore case)"},
                    {"key": "regex", "display": "Regex Match (case-sensitive)"},
                    {"key": "iregex", "display": "Regex Match (ignore case)"},
                    {"key": "isempty", "display": "Is Empty"},
                    {"key": "isnull", "display": "Is NULL"},
                ],
                "bool": [
                    {"key": "istrue", "display": "Is TRUE"},
                    {"key": "isfalse", "display": "Is FALSE"},
                    {"key": "isnull", "display": "Is NULL"},
                ],
                "numeric": [
                    {"key": "exact", "display": "Equals (numeric)"},
                    {"key": "lt", "display": "Less Than"},
                    {"key": "gt", "display": "Greater Than"},
                    {"key": "lte", "display": "Less Than or Equal To"},
                    {"key": "gte", "display": "Greater Than or Equal To"},
                    {"key": "isnull", "display": "Is NULL"},
                ],
            },
            operators,
        )

    @patch("model_filters.utilities.get_fields_from_path")
    def test_get_field_values(self, mock_get_fields):
        """Get values for a field."""
        model = Mock()
        field_paths = ["name", "description", "status"]
        get_fields_side_effect = [
            [Mock(spec=[])],
            [Mock(choices=[])],
            [Mock(choices=[(2, "TWO"), (1, "ONE"), (3, "THREE")])],
        ]
        mock_get_fields.side_effect = get_fields_side_effect
        values = utilities.get_field_values(model, field_paths)
        self.assertEqual(
            {
                "status": [
                    {"key": 2, "display": "TWO (2)"},
                    {"key": 1, "display": "ONE (1)"},
                    {"key": 3, "display": "THREE (3)"},
                ]
            },
            values,
        )
        mock_get_fields.side_effect = get_fields_side_effect
        values = utilities.get_field_values(
            model,
            field_paths,
            append_choice_value=False,
            sort_values=True,
        )
        self.assertEqual(
            {
                "status": [
                    {"key": 1, "display": "ONE"},
                    {"key": 2, "display": "TWO"},
                    {"key": 3, "display": "THREE"},
                ]
            },
            values,
        )

    @patch("model_filters.utilities.get_field_values")
    @patch("model_filters.utilities.get_field_operators")
    @patch("model_filters.utilities.get_clean_filter_fields")
    @patch("model_filters.utilities.admin.site._registry")
    def test_get_field_data(
        self,
        mock_registry,
        mock_get_clean_filter_fields,
        mock_get_field_operators,
        mock_get_field_values,
    ):
        """Build data dict for model field."""
        model = Mock()
        model_admin = Mock(get_model_filter_fields=Mock(side_effect=[("field1",)]))
        mock_registry.get = Mock(side_effect=[model_admin, None])
        clean_filter_fields = {"field1": "Field 1"}
        mock_get_clean_filter_fields.return_value = clean_filter_fields
        field_operators = {"field1": ["exact"]}
        mock_get_field_operators.return_value = field_operators
        field_values = {"field1": ["a", "b", "c"]}
        mock_get_field_values.return_value = field_values
        data = utilities.get_field_data(model, Mock())
        self.assertEqual(
            dict(
                field_choices=clean_filter_fields,
                field_operators=field_operators,
                field_values=field_values,
            ),
            data,
        )
        # Second call raises "AttributeError" from registry.
        data = utilities.get_field_data(model, Mock())
        self.assertEqual(
            dict(
                field_choices=clean_filter_fields,
                field_operators=field_operators,
                field_values=field_values,
            ),
            data,
        )

    @patch("model_filters.utilities.settings")
    @patch("model_filters.utilities.get_apply_url")
    @patch("model_filters.utilities.get_field_data")
    def test_update_context(self, mock_field_data, mock_apply_url, mock_settings):
        """Context data should have necessary data."""
        model_filter = Mock()
        initial_context = dict(
            field_operators=[{"key": "key", "value": "value"}],
            field_values=[{"key": "key", "value": "value"}],
            form_url="http://mock_url",
        )
        content_type = Mock(id=42)
        change_form = Mock()
        field_form = Mock()
        mock_field_data.return_value = {"mock_field_data": "mock_field_data"}
        mock_apply_url.return_value = "mock_apply_filter_url"
        mock_settings.INSTALLED_APPS = ["grappelli"]

        context = utilities.update_context(
            model_filter, dict(initial_context), content_type, change_form, field_form
        )
        expected = dict(
            mock_field_data="mock_field_data",
            field_operators='[{"key": "key", "value": "value"}]',
            field_values='[{"key": "key", "value": "value"}]',
            form_url="http://mock_url?content_type=42",
            apply_filter_url="mock_apply_filter_url",
            using_grappelli=True,
            change_form_template=change_form,
        )
        self.assertEqual(expected, context)

        context = utilities.update_context(
            None, dict(initial_context), content_type, change_form, field_form
        )
        del expected["apply_filter_url"]
        self.assertEqual(expected, context)

    @patch("model_filters.utilities.make_query_filter")
    def test_build_query_filter(self, mock_make_filter):
        """Build a complete query filter (simple)."""
        fields = [
            Mock(field="name", operator="exact", value="Tornado Seeds", negate=False),
        ]
        results = [Q(name__exact="Tornado Seeds")]
        model_filter = Mock(fields=Mock(all=Mock(return_value=fields)))
        mock_make_filter.side_effect = results
        final_filter = utilities.build_query_filter(model_filter)
        self.assertEqual(Q(name__exact="Tornado Seeds"), final_filter)

    @patch("model_filters.utilities.make_query_filter")
    def test_build_query_filter_and(self, mock_make_filter):
        """Build a complete query filter (and)."""
        fields = [
            Mock(field="name", operator="exact", value="Tornado Seeds", negate=False),
            Mock(
                field="description",
                operator="contains",
                value="Just add water",
                negate=False,
            ),
        ]
        results = [
            Q(name__exact="Tornado Seeds"),
            Q(description__contains="Just add water"),
        ]
        model_filter = Mock(fields=Mock(all=Mock(return_value=fields)))
        mock_make_filter.side_effect = results
        final_filter = utilities.build_query_filter(model_filter)
        self.assertEqual(
            Q(name__exact="Tornado Seeds") & Q(description__contains="Just add water"),
            final_filter,
        )

    @patch("model_filters.utilities.make_query_filter")
    def test_build_query_filter_or(self, mock_make_filter):
        """Build a complete query filter (or)."""
        fields = [
            Mock(field="name", operator="exact", value="Tornado Seeds", negate=False),
            Mock(field=constants.OR_SEPARATOR, operator="exact", value=""),
            Mock(
                field="description",
                operator="contains",
                value="Just add water",
                negate=False,
            ),
            Mock(field="code", operator="exact", value="TS", negate=True),
        ]
        results = [
            Q(name__exact="Tornado Seeds"),
            Q(description__contains="Just add water"),
            ~Q(code__exact="TS"),
        ]
        model_filter = Mock(fields=Mock(all=Mock(return_value=fields)))
        mock_make_filter.side_effect = results
        final_filter = utilities.build_query_filter(model_filter)
        self.assertEqual(
            Q(name__exact="Tornado Seeds")
            | (Q(description__contains="Just add water") & ~Q(code__exact="TS")),
            final_filter,
        )

    @patch("model_filters.utilities.build_query_params")
    def test_make_query_filter(self, mock_build_params):
        """Build query filter from param dictionary."""
        mock_build_params.return_value = {"name__exact": "Tornado Seeds"}
        field = Mock(field="name", negate=False)
        query = utilities.make_query_filter(field)
        self.assertEqual(Q(name__exact="Tornado Seeds"), query)
        field = Mock(field="name", negate=True)
        query = utilities.make_query_filter(field)
        self.assertEqual(~Q(name__exact="Tornado Seeds"), query)

    @patch("model_filters.utilities.get_fields_from_path")
    def test_build_query_params(self, mock_get_fields):
        """Build query params from field filter."""
        easy_pickings = [
            (constants.IS_NULL, None),
            (constants.IS_TRUE, True),
            (constants.IS_FALSE, False),
            (constants.IS_EMPTY, ""),
        ]
        for easy_picking in easy_pickings:
            field = Mock(field="name", operator=easy_picking[0])
            params = utilities.build_query_params(field)
            self.assertEqual({field.field: easy_picking[1]}, params)

        mock_get_fields.return_value = [Mock(to_python=Mock(return_value="XYZ"))]
        field = Mock(field="name", operator="exact")
        params = utilities.build_query_params(field)
        self.assertEqual({"name__exact": "XYZ"}, params)

    @patch("model_filters.utilities.reverse")
    def test_get_apply_url(self, mock_reverse):
        """Build apply model filter URL."""
        content_type = Mock(app_label="mockapp", model="mockmodel")
        model_filter_id = "mock"
        mock_reverse.return_value = "http://mock_url"
        url = utilities.get_apply_url(content_type, model_filter_id)
        self.assertEqual("http://mock_url?__model_filter=mock", url)
        self.assertEqual(
            mock_reverse.call_args_list[0][0][0], "admin:mockapp_mockmodel_changelist"
        )

    def test_user_can_access_content_type(self):
        """Basic content type access check."""
        user = Mock(has_perm=Mock(side_effect=[False, False]))
        self.assertFalse(utilities.user_can_access_content_type(user, Mock()))
        self.assertEqual(2, user.has_perm.call_count)
        user = Mock(has_perm=Mock(side_effect=[True, False]))
        self.assertTrue(utilities.user_can_access_content_type(user, Mock()))
        user = Mock(has_perm=Mock(side_effect=[False, True]))
        self.assertTrue(utilities.user_can_access_content_type(user, Mock()))
        user = Mock(has_perm=Mock(side_effect=[True, True]))
        self.assertTrue(utilities.user_can_access_content_type(user, Mock()))

    @patch("model_filters.utilities.settings")
    @patch("model_filters.utilities.user_can_access_content_type")
    def test_user_has_permission(self, mock_user_access, mock_settings):
        """Basic user permissions check."""
        mock_user_access.return_value = False
        user = Mock(is_superuser=False)
        setting_name = "SNAFU"

        self.assertTrue(
            utilities.user_has_permission(
                Mock(is_superuser=False), setting_name, True, model_filter=None
            )
        )
        self.assertTrue(
            utilities.user_has_permission(
                Mock(is_superuser=True), setting_name, True, model_filter=Mock()
            )
        )

        mock_user_access.return_value = False
        self.assertFalse(
            utilities.user_has_permission(
                user, setting_name, True, model_filter=Mock(owner=None)
            )
        )

        mock_user_access.return_value = True
        self.assertTrue(
            utilities.user_has_permission(
                user, setting_name, True, model_filter=Mock(owner=user)
            )
        )

        setattr(mock_settings, setting_name, True)
        self.assertFalse(
            utilities.user_has_permission(
                user, setting_name, True, model_filter=Mock(owner=None)
            )
        )

        setattr(mock_settings, setting_name, False)
        self.assertIsNone(
            utilities.user_has_permission(
                user, setting_name, True, model_filter=Mock(owner=None)
            )
        )

    def test_use_guardian(self):
        """Use guardian if available."""
        with override_settings(MODEL_FILTERS_USE_GUARDIAN=False):
            with modify_settings(INSTALLED_APPS={"remove": ["guardian"]}):
                self.assertFalse(utilities.use_guardian())
        with override_settings(MODEL_FILTERS_USE_GUARDIAN=True):
            with modify_settings(INSTALLED_APPS={"remove": ["guardian"]}):
                self.assertFalse(utilities.use_guardian())
        with override_settings(MODEL_FILTERS_USE_GUARDIAN=False):
            with modify_settings(INSTALLED_APPS={"append": ["guardian"]}):
                self.assertFalse(utilities.use_guardian())
        with override_settings(MODEL_FILTERS_USE_GUARDIAN=True):
            with modify_settings(INSTALLED_APPS={"append": ["guardian"]}):
                self.assertTrue(utilities.use_guardian())
