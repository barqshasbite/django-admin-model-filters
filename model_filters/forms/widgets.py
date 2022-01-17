# coding=utf-8

"""Form widgets."""

from django import forms


class FieldSelect(forms.Select):
    """Field select widget."""

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """Add a 'title' to the <option> elements.

        The title is set as the 'value' so that it is not totally obscured from
        view.
        """
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        option["attrs"]["title"] = value
        return option
