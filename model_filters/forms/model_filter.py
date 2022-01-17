# coding=utf-8

"""Model filter forms."""

from typing import Optional

from django import forms

from model_filters.models import ModelFilter


class ModelFilterForm(forms.ModelForm):
    """Model filter form."""

    help_template = "admin/model_filters/help.html"

    def __init__(self, *args, **kwargs):
        """Create the form with a proper field configuration."""
        super().__init__(*args, **kwargs)
        if "description" in self.fields:
            self.fields["description"].widget.attrs["rows"] = 2
        if "content_type" in self.fields:
            self.restrict_field(self.fields["content_type"])
            self._update_content_type_choices()
        if "owner" in self.fields:
            self.restrict_field(self.fields["owner"])
            self._update_owner_choices()

    @staticmethod
    def restrict_field(field):
        """Prevent a related field from being interacted with."""
        field.empty_label = None
        field.widget.can_add_related = False
        field.widget.can_change_related = False
        field.widget.can_delete_related = False

    def _update_content_type_choices(self):
        """New model filters are pinned to a single content type choice."""
        self._update_choices(self._get_content_type(), "content_type")

    def _update_owner_choices(self):
        """New model filters are pinned to a single owner choice."""
        self._update_choices(self._get_owner(), "owner")

    def _update_choices(self, object_id, field_name):
        """Pin the choices for a field to the provided ID."""
        if object_id:
            queryset = self.fields[field_name].queryset
            self.fields[field_name].queryset = queryset.filter(id=object_id)
        else:
            self.fields[field_name].choices = []

    def _get_content_type(self) -> Optional[str]:
        """Get the content type ID for the model filter."""
        if self.instance.pk:
            return self.instance.content_type_id
        return self.initial.get("content_type", self.data.get("content_type"))

    def _get_owner(self) -> Optional[str]:
        """Get the owner ID for the model filter."""
        if self.instance.pk:
            return self.instance.owner_id
        return self.initial.get("owner", self.data.get("owner"))

    class Meta:
        """Model form configuration."""

        model = ModelFilter
        fields = (
            "name",
            "description",
            "content_type",
            "owner",
        )

    class Media:
        """Custom media."""

        css = {
            "screen": [
                "model-filters/model-filters.css",
            ]
        }
        js = [
            "model-filters/model-filters.js",
        ]
