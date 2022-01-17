# coding=utf-8

"""Field filter inline forms."""

from typing import Dict

from django import forms
from django.utils.translation import gettext_lazy as _

from model_filters.constants import OR_SEPARATOR
from model_filters.forms.field_filter import FieldFilterForm
from model_filters.utilities import get_field_data


class FieldFilterInlineFormset(forms.BaseInlineFormSet):
    """Custom inline formset for field filters."""

    form = FieldFilterForm

    def __init__(self, *args, **kwargs):
        """Create the inline formset.

        The `model_filter_content_type` attribute is set on the inline formset
        class by the `get_formsets_with_inlines` method on the parent model
        admin, `ModelFilterAdmin`. Since the formset class is created on-the-fly
        with a class factory there should not be any conflicts or issues with
        thread safety when using a class level attribute.
        """
        form_kwargs = kwargs.pop("form_kwargs", {})
        form_kwargs.update(self._build_form_kwargs())
        super().__init__(*args, form_kwargs=form_kwargs, **kwargs)

    def _build_form_kwargs(self) -> Dict:
        """Setup keyword arguments to pass to inline forms."""
        content_type = self.model_filter_content_type  # pylint: disable=no-member
        kwargs = get_field_data(content_type.model_class(), self.form)
        kwargs["model"] = content_type.model_class()
        return kwargs

    def clean(self):
        """Ensure the filter fields are valid."""
        super().clean()
        if self.is_valid() and not any(self.errors):
            self.clean_field_filters(self.cleaned_data)

    @staticmethod
    def clean_field_filters(cleaned_data):
        """Validate the field filter formset data."""
        filters = [data for data in cleaned_data if not data.get("DELETE", False)]
        if len(filters) == 0:
            raise forms.ValidationError(_("At least one field filter is required."))
        if filters[0].get("field") == OR_SEPARATOR:
            raise forms.ValidationError(
                _("First field filter cannot be an OR separator.")
            )
        if filters[-1].get("field") == OR_SEPARATOR:
            raise forms.ValidationError(
                _("Last field filter cannot be an OR separator.")
            )
        last_filter_was_or = False
        for field_filter in filters:
            if field_filter.get("field") == OR_SEPARATOR:
                if last_filter_was_or:
                    raise forms.ValidationError(
                        _("Cannot have consecutive OR separators.")
                    )
                last_filter_was_or = True
            else:
                last_filter_was_or = False
