# coding=utf-8

"""Field filter form."""

from typing import Any, Dict, List, OrderedDict, Tuple

from django import forms
from django.contrib.admin.utils import get_fields_from_path
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from model_filters.constants import IS_EMPTY, IS_FALSE, IS_NULL, IS_TRUE, OR_SEPARATOR
from model_filters.forms.widgets import FieldSelect
from model_filters.models import FieldFilter


class FieldFilterForm(forms.ModelForm):
    """Field filter configuration form."""

    DEFAULT_OPERATORS = [
        ("exact", _("Equals (exact)")),
        (IS_NULL, _("Is NULL")),
    ]

    BOOLEAN_OPERATORS = [
        (IS_TRUE, _("Is TRUE")),
        (IS_FALSE, _("Is FALSE")),
        (IS_NULL, _("Is NULL")),
    ]

    TEXT_OPERATORS = [
        ("exact", _("Equals (case-sensitive)")),
        ("iexact", _("Equals (ignore case)")),
        ("contains", _("Contains (case-sensitive)")),
        ("icontains", _("Contains (ignore case)")),
        ("regex", _("Regex Match (case-sensitive)")),
        ("iregex", _("Regex Match (ignore case)")),
        (IS_EMPTY, _("Is Empty")),
        (IS_NULL, _("Is NULL")),
    ]

    NUMERIC_OPERATORS = [
        ("exact", _("Equals (numeric)")),
        ("lt", _("Less Than")),
        ("gt", _("Greater Than")),
        ("lte", _("Less Than or Equal To")),
        ("gte", _("Greater Than or Equal To")),
        (IS_NULL, _("Is NULL")),
    ]

    DATE_OPERATORS = [
        ("exact", _("Equals (date/time)")),
        ("lt", _("Less Than")),
        ("gt", _("Greater Than")),
        ("lte", _("Less Than or Equal To")),
        ("gte", _("Greater Than or Equal To")),
        (IS_NULL, _("Is NULL")),
    ]

    UUID_OPERATORS = [
        ("exact", _("Equals (UUID)")),
        (IS_NULL, _("Is NULL")),
    ]

    # For choices validation only.
    OPERATORS = (
        BOOLEAN_OPERATORS
        + TEXT_OPERATORS
        + NUMERIC_OPERATORS
        + DATE_OPERATORS
        + UUID_OPERATORS
    )

    # Operators that can be used with no value.
    NO_VALUE_OPERATORS = [
        IS_NULL,
        IS_TRUE,
        IS_FALSE,
        IS_EMPTY,
        OR_SEPARATOR,
    ]

    # Mapping of field classes to valid operators.
    OPERATOR_MAP = {
        models.CharField: TEXT_OPERATORS,
        models.TextField: TEXT_OPERATORS,
        models.FilePathField: TEXT_OPERATORS,
        models.IPAddressField: TEXT_OPERATORS,
        models.GenericIPAddressField: TEXT_OPERATORS,
        models.DecimalField: NUMERIC_OPERATORS,
        models.FloatField: NUMERIC_OPERATORS,
        models.IntegerField: NUMERIC_OPERATORS,
        models.DateField: DATE_OPERATORS,
        models.BooleanField: BOOLEAN_OPERATORS,
        models.UUIDField: UUID_OPERATORS,
    }

    # Extra choices to append to the field choices.
    EXTRA_FIELD_CHOICES = [
        (OR_SEPARATOR, _("--- OR ---")),
    ]

    field = forms.ChoiceField(
        label=_("Field"),
        required=True,
        widget=FieldSelect(attrs={"class": "af-query-field"}),
        help_text=_("Field to filter."),
    )
    operator = forms.ChoiceField(
        label=_("Operator"),
        required=True,
        choices=OPERATORS,
        initial="exact",
        widget=forms.Select(attrs={"class": "af-query-operator"}),
        help_text=_("Operator"),
    )
    value = forms.CharField(
        label=_("Value"),
        required=True,
        widget=forms.TextInput(attrs={"class": "af-query-value"}),
    )
    negate = forms.BooleanField(
        label=_("Negate"),
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "af-query-negate"}),
    )

    class Meta:
        """Model form configuration."""

        model = FieldFilter
        fields = [
            "field",
            "operator",
            "value",
            "negate",
        ]

    def __init__(
        self,
        *args,
        model: models.Model = None,
        field_choices: OrderedDict[str, str] = None,
        field_operators: Dict[str, List[Dict[str, str]]] = None,
        field_values: Dict[str, List[Dict[str, str]]] = None,
        **kwargs,
    ):
        """Create the field filter form."""
        super().__init__(*args, **kwargs)
        if field_choices is None:
            field_choices = {}
        if field_operators is None:
            field_operators = {}
        if field_values is None:
            field_values = {}
        self.model = model
        self.field_operators = field_operators
        self.field_values = field_values
        self.fields["field"].choices = self._build_field_choices(field_choices)

    def _build_field_choices(self, fields: Dict) -> List[Tuple[str, str]]:
        """Create a list of valid choices for the `field` field."""
        return list(fields.items()) + self.EXTRA_FIELD_CHOICES

    def clean(self):
        """Clean the form."""
        cleaned_data = super().clean()
        cleaned_data["operator"] = self._clean_operator(cleaned_data)
        cleaned_data["value"] = self._clean_value(cleaned_data)
        return cleaned_data

    def _clean_value(self, cleaned_data: Dict) -> Any:
        """Ensure the value string can be cast to the field's type.

        The value form field is a CharField, so we will not get any proper
        field validation for values based on their actual types.

        This method will convert the provided value to a new value using the
        fields built-in conversion methods, allowing proper data validation.
        """
        field_path = cleaned_data.get("field")
        if not field_path:
            return None
        operator = cleaned_data.get("operator")
        if not operator:
            return None
        if field_path == OR_SEPARATOR or operator in self.NO_VALUE_OPERATORS:
            self.fields["value"].required = False
            self.errors.pop("value", None)
            return ""
        value = cleaned_data.get("value")
        if not value:
            return value
        field = get_fields_from_path(self.model, field_path)[-1]
        try:
            field.to_python(value)
        except Exception as error:  # pylint: disable=broad-except
            message = str(error)
            if isinstance(error, ValidationError):
                message = " ".join(error.messages)
            self.add_error(
                "value",
                _("Value is not valid for field ({field_type}): {msg}").format(
                    field_type=field.get_internal_type(), msg=message
                ),
            )
        return value

    def _clean_operator(self, cleaned_data):
        """Ensure operator value is valid for field."""
        field = cleaned_data.get("field")
        if field is None:
            return None
        operator = cleaned_data.get("operator")
        if not operator:
            return None
        if field != OR_SEPARATOR:
            operator_dicts = self.field_operators.get(field, [])
            if not any(operator == od["key"] for od in operator_dicts):
                self.add_error(
                    "operator",
                    _("Operator '{operator}' is not allowed for this field.").format(
                        operator=operator
                    ),
                )
        return operator
