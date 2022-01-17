# coding=utf-8

"""Model filter admin mixins."""

from typing import Dict, Optional

from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest

from model_filters.admin.list_filters import ModelFilterListFilter
from model_filters.forms.model_filter import ModelFilterForm
from model_filters.utilities import change_owner_only, use_guardian


class ModelFilterMixin:
    """Mixin to provide the default model filter behavior."""

    default_change_list_template = "admin/change_list.html"
    model_filter_change_list_template = "admin/model_filters/custom_change_list.html"
    model_filter_fields = ()
    model_filter_form = ModelFilterForm
    model_filter_list_filter = ModelFilterListFilter

    def __init__(self, *args, **kwargs):
        """Setup necessary parameters for model filtering."""
        super().__init__(*args, **kwargs)
        self._setup_change_list_template()

    def _setup_change_list_template(self):
        """Determine the change list template to extend.

        Since a `ModelAdmin` can define it's own `change_list_template`, we
        must ensure that we extend the correct template to maintain the proper
        template hierarchy.
        """
        self.extend_change_list_template = self.default_change_list_template
        if getattr(self, "change_list_template", None):
            # Store preset template for later use.
            self.extend_change_list_template = self.change_list_template
        # Replace any preset template with ours.
        self.change_list_template = self.model_filter_change_list_template

    def get_list_filter(self, request: HttpRequest):
        """Put the model filters list filter at the top."""
        return (self.model_filter_list_filter,) + tuple(self.list_filter)

    def get_model_filter_fields(self):
        """Return the configured list of model filter fields."""
        return self.model_filter_fields

    def update_extra_context(
        self, request: HttpRequest, extra_context: Optional[Dict]
    ) -> Dict:
        """Get the extra context to pass to the changelist view template."""
        extra_context = {} if extra_context is None else extra_context
        extra_context.update(
            {
                "change_list_template": self.extend_change_list_template,
                "content_type": ContentType.objects.get_for_model(self.model),
                "current_model_filter": request.GET.get(
                    ModelFilterListFilter.parameter_name
                ),
            }
        )
        return extra_context

    def changelist_view(
        self, request: HttpRequest, extra_context: Optional[Dict] = None
    ):
        """Add extra context to the changelist view."""
        extra_context = self.update_extra_context(request, extra_context)
        # Store the extra context on the request for later use.
        request.model_filter_extra_context = extra_context
        return super().changelist_view(request, extra_context=extra_context)

    def get_changelist_instance(self, request):
        """Update the extra context with data from the list filter.

        This is called from within `changelist_view`, and further updates
        the extra context. Specifically, whether or not the current user
        has permissions to edit the currently selected model filter.
        """
        changelist = super().get_changelist_instance(request)
        model_filter = getattr(request, "model_filter_model_filter", None)
        if model_filter:
            can_change_filter = model_filter.owner == request.user
            if not can_change_filter and not change_owner_only():
                # Look for "change" permissions with the permission framework.
                codename = get_permission_codename("change", model_filter._meta)
                can_change_filter = request.user.has_perm(
                    f"{model_filter._meta.app_label}.{codename}",
                    obj=model_filter if use_guardian() else None,
                )
            extra_context = request.model_filter_extra_context
            extra_context["can_change_filter"] = can_change_filter
        return changelist
