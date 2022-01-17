# coding=utf-8

"""Application utilities."""

import collections
import json
from functools import reduce
from operator import or_
from typing import Dict, Iterable, List, Optional, OrderedDict, Tuple, Type, Union

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.utils import get_fields_from_path
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template.defaultfilters import title
from django.urls import reverse

from model_filters import constants


def get_clean_filter_fields(
    model: Type[models.Model],
    fields: List[Union[str, Tuple[str, str]]],
    use_title_case: bool = True,
) -> OrderedDict[str, str]:
    """Convert a list of `model_filter_fields` into a clean lookup table.

    The lookup table consists of the field name as the key, and the value
    is the verbose name for display. Field names can also span relations
    using the `__` lookup notation.

    If the field is a string, do a field lookup to get the verbose name.
    If the field is a tuple, use the second element as the verbose name.

    :param model: The model the fields are on or are reachable from.
    :param fields: The field values to clean.
    :param use_title_case: Convert the display name to title case.
    :return: A lookup table of field names to verbose names.
    """
    model_fields = collections.OrderedDict()
    for field in fields:
        if isinstance(field, (tuple, list)):
            if len(field) != 2:
                raise ValueError("Iterable model filter field length must be 2.")
            if not (isinstance(field[0], str) and isinstance(field[1], str)):
                raise ValueError("Model filter field values must be strings.")
            field, verbose_name = field[0], field[1]
        elif not isinstance(field, str):
            raise ValueError("Model filter field values must be strings.")
        else:
            model_field = get_fields_from_path(model, field)[-1]
            verbose_name = model_field.verbose_name
            if use_title_case:
                verbose_name = title(verbose_name)
        model_fields[field] = verbose_name
    return model_fields


def get_field_operators(
    model: Type[models.Model],
    field_paths: Iterable[str],
    field_form,
) -> Dict[str, List[Dict[str, str]]]:
    """Create a mapping of field paths to allowed operators.

    First looks for an exact match of the field in the operator map. If not
    found, uses an `isinstance` check, which will match on the first subclass.
    If no match is found, the field will get the default operators.

    :param model: The model the fields are on or are reachable from.
    :param field_paths: The fields to get the operators for.
    :param field_form: The field filter form being used.
    :type field_form: model_filters.forms.field_filter.FieldFilterForm
    :return: Map of operators for the fields.
    """
    field_operators = {}
    for field_path in field_paths:
        field_obj = get_fields_from_path(model, field_path)[-1]
        operators = None
        for field_class, valid_operators in field_form.OPERATOR_MAP.items():
            # pylint: disable=unidiomatic-typecheck
            if type(field_obj) == field_class:
                operators = valid_operators
                break
            if not operators and isinstance(field_obj, field_class):
                operators = valid_operators
        if not operators:
            operators = field_form.DEFAULT_OPERATORS
        field_operators[field_path] = [
            {"key": operator[0], "display": str(operator[1])} for operator in operators
        ]
    return field_operators


def get_field_values(
    model: Type[models.Model],
    field_paths: Iterable[str],
    valid_choice_types=(list, tuple),
    append_choice_value: bool = True,
    sort_values: bool = False,
) -> Dict[str, List[Dict[str, str]]]:
    """Create a mapping of field paths to allowed values.

    :param model: The model the fields are on or are reachable from.
    :param field_paths: The fields to get the values for.
    :param valid_choice_types: The allowed types of model field `choices`.
    :param append_choice_value: Add the choice value to the display.
    :param sort_values: Sort the field values
    :return: Map of values for the fields.
    """
    field_values = {}
    for field_path in field_paths:
        field_obj = get_fields_from_path(model, field_path)[-1]
        if hasattr(field_obj, "choices"):
            choices = field_obj.choices
            if choices and isinstance(choices, valid_choice_types):
                field_values[field_path] = [
                    {
                        "key": choice[0],
                        "display": f"{choice[1]} ({choice[0]})"
                        if append_choice_value
                        else choice[1],
                    }
                    for choice in choices
                ]
                if sort_values:
                    field_values[field_path] = sorted(
                        field_values[field_path], key=lambda i: str(i["key"]).lower()
                    )
    return field_values


def get_field_data(model: models.Model, field_form) -> Dict:
    """Return model filter field data for a model.

    :param model: The model the fields are on or are reachable from.
    :param field_form: The field filter form being used.
    :type field_form: model_filters.forms.field_filter.FieldFilterForm
    """
    # Sort out the model fields that can be filtered.
    try:
        model_admin = admin.site._registry.get(model)
        raw_filter_fields = model_admin.get_model_filter_fields()
    except AttributeError:
        raw_filter_fields = ()
    clean_filter_fields = get_clean_filter_fields(model, raw_filter_fields)
    field_paths = list(clean_filter_fields.keys())
    # Sort out the allowed operators and values for the fields.
    field_operators = get_field_operators(
        model=model, field_paths=field_paths, field_form=field_form
    )
    field_values = get_field_values(model=model, field_paths=field_paths)
    # Return the extra form data.
    return dict(
        field_choices=clean_filter_fields,
        field_operators=field_operators,
        field_values=field_values,
    )


def update_context(
    model_filter,
    context: Dict,
    content_type: ContentType,
    change_form: str,
    field_form,
) -> Dict:
    """Update the extra context being passed to the templates.

    :param model_filter: Optional model filter.
    :type model_filter: model_filters.models.ModelFilter
    :param context: Context to update.
    :param content_type: Model filter content type.
    :param change_form: Change form to use.
    :param field_form: The field filter form being used.
    :type field_form: model_filters.forms.field_filter.FieldFilterForm
    """
    context.update(get_field_data(content_type.model_class(), field_form))
    context["field_operators"] = json.dumps(context["field_operators"])
    context["field_values"] = json.dumps(context["field_values"])
    context["form_url"] = f"{context['form_url']}?content_type={content_type.id}"
    if model_filter:
        context["apply_filter_url"] = get_apply_url(content_type, model_filter.id)
    context["using_grappelli"] = "grappelli" in settings.INSTALLED_APPS
    context["change_form_template"] = change_form
    return context


def build_query_filter(model_filter) -> models.Q:
    """Build a complete query filter for a model filter.

    :param model_filter: Model filter to build Q object for.
    :type model_filter: model_filters.models.ModelFilter
    :return: A query filter for all filter fields in the model filter.
    """
    query_to_and = models.Q()
    queries_to_or = []
    for field in model_filter.fields.all():
        if field.field == constants.OR_SEPARATOR:
            queries_to_or.append(query_to_and)
            query_to_and = models.Q()
        else:
            query_to_and = query_to_and & make_query_filter(field)
    if queries_to_or:
        queries_to_or.append(query_to_and)
        query_to_and = reduce(or_, queries_to_or)
    return query_to_and


def make_query_filter(field) -> models.Q:
    """Create a query filter from a filter field."""
    query = models.Q()
    query_params = build_query_params(field)
    if field.negate:
        query = query & ~models.Q(**query_params)
    else:
        query = query & models.Q(**query_params)
    return query


def build_query_params(field) -> Dict:
    """Build query params from a field filter.

    :param field: A field filter.
    :type field: model_filters.models.FieldFilter
    """
    if field.operator == constants.IS_NULL:
        query_params = {field.field: None}
    elif field.operator == constants.IS_EMPTY:
        query_params = {field.field: ""}
    elif field.operator == constants.IS_TRUE:
        query_params = {field.field: True}
    elif field.operator == constants.IS_FALSE:
        query_params = {field.field: False}
    else:
        model_field = get_fields_from_path(
            field.model_filter.content_type.model_class(), field.field
        )[-1]
        query_params = {
            f"{field.field}__{field.operator}": model_field.to_python(field.value),
        }
    return query_params


def get_apply_url(content_type: ContentType, model_filter_id: int) -> str:
    """Get the URL used to apply a model filter."""
    app = content_type.app_label
    model_name = content_type.model
    url = reverse(f"admin:{app}_{model_name}_changelist")
    url = f"{url}?{constants.FILTER_PARAMETER_NAME}={model_filter_id}"
    return url


def user_can_access_content_type(user: AbstractUser, content_type: ContentType) -> bool:
    """Determine if a user can access a content type."""
    opts = content_type.model_class()._meta
    has_view_perm = user.has_perm(
        f"{opts.app_label}.{get_permission_codename('view', opts)}"
    )
    has_change_perm = user.has_perm(
        f"{opts.app_label}.{get_permission_codename('change', opts)}"
    )
    return has_view_perm or has_change_perm


def user_has_permission(
    user: AbstractUser,
    setting: str,
    default: bool,
    model_filter=None,
) -> Optional[bool]:
    """Check if a user has permission on the model filter.

    :param user: User to check permissions for.
    :param setting: Setting name to check.
    :param default: Default value for setting.
    :param model_filter: Model filter being accessed.
    :type model_filter: model_filters.models.ModelFilter
    """
    if user.is_superuser or model_filter is None:
        return True
    if not user_can_access_content_type(user, model_filter.content_type):
        return False
    if user == model_filter.owner:
        return True
    if getattr(settings, setting, default):
        return False
    return None


def use_guardian() -> bool:
    """Check if we should use guardian for object level permissions."""
    return (
        getattr(
            settings,
            constants.SETTING_MODEL_FILTERS_USE_GUARDIAN,
            constants.DEFAULT_MODEL_FILTERS_USE_GUARDIAN,
        )
        and "guardian" in getattr(settings, "INSTALLED_APPS", [])
    )


def view_owner_only() -> bool:
    """Only owners can view a model filter."""
    return getattr(
        settings,
        constants.SETTING_MODEL_FILTERS_VIEW_OWNER_ONLY,
        constants.DEFAULT_MODEL_FILTERS_VIEW_OWNER_ONLY,
    )


def change_owner_only() -> bool:
    """Only owners can change a model filter."""
    return getattr(
        settings,
        constants.SETTING_MODEL_FILTERS_CHANGE_OWNER_ONLY,
        constants.DEFAULT_MODEL_FILTERS_CHANGE_OWNER_ONLY,
    )
