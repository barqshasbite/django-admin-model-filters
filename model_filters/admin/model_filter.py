# coding=utf-8

"""Model filter administration."""

from typing import Dict, List, Optional, Union

from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.db.models.functions import Lower
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from model_filters import constants
from model_filters.admin.field_filter_inline import FieldFilterTabularInline
from model_filters.admin.list_filters import OwnerListFilter
from model_filters.forms.model_filter import ModelFilterForm
from model_filters.models import ModelFilter
from model_filters.utilities import (
    get_apply_url,
    update_context,
    use_guardian,
    user_can_access_content_type,
    user_has_permission,
)


# pylint: disable=ungrouped-imports
try:
    from guardian.admin import GuardedModelAdmin
except (ImportError, RuntimeError):
    from django.contrib.admin import ModelAdmin as GuardedModelAdmin


class ModelFilterAdminBase(admin.ModelAdmin):
    """Manage the model filter models."""

    form = ModelFilterForm
    field_filter_inline = FieldFilterTabularInline
    add_form_template = "admin/model_filters/custom_change_form.html"
    change_list_template = "admin/model_filters/modelfilter/custom_change_list.html"
    default_change_form_template = "admin/change_form.html"
    model_filter_change_form_template = "admin/model_filters/custom_change_form.html"

    list_display = [
        "id",
        "created",
        "name",
        "description",
        "content_type",
        "owner",
    ]
    list_display_links = [
        "id",
        "created",
        "name",
    ]
    list_filter = [
        OwnerListFilter,
        "created",
        "content_type",
    ]
    list_select_related = [
        "content_type",
    ]
    ordering = [
        Lower("name"),
    ]
    fields = [
        "name",
        "description",
        "content_type",
        "owner",
        "created",
    ]
    readonly_fields = [
        "created",
    ]

    def __init__(self, model, admin_site):
        """Create the model admin."""
        super().__init__(model, admin_site)
        self._setup_change_form_template()

    def _setup_change_form_template(self):
        """Determine the change form template to extend.

        Since a `ModelAdmin` can define it's own `change_form_template`, we
        must ensure that we extend the correct template to maintain the proper
        template hierarchy.
        """
        self.extend_change_form_template = self.default_change_form_template
        if getattr(self, "change_form_template", None):
            # Store preset template for later use.
            self.extend_change_form_template = self.change_form_template
        # Replace any preset template with ours.
        self.change_form_template = self.model_filter_change_form_template

    def get_inlines(self, request: HttpRequest, obj: ModelFilter) -> List:
        """Get change form inlines."""
        return [self.field_filter_inline]

    @property
    def inlines(self):
        """Return inlines via `get_inlines()`.

        Deprecated: Remove when Django 2.2 support is dropped.
        """
        return self.get_inlines(None, None)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Entry point into the change form for a model filter.

        Immediately parses the GET params for a `content_type` if no `object_id`
        is present. The content type is then stored on the `request` for later
        use.
        """
        if object_id is None:
            self.set_content_type(request, self._get_content_type(request))
        return super().changeform_view(
            request, object_id=object_id, form_url=form_url, extra_context=extra_context
        )

    @staticmethod
    def _get_content_type(request: HttpRequest) -> ContentType:
        """Get the content type for the model filter."""
        try:
            return get_object_or_404(
                ContentType, id=int(request.GET.get("content_type"))
            )
        except (ValueError, TypeError) as error:
            raise Http404("Unknown content type.") from error

    def get_object(self, request, object_id, from_field=None):
        """First fetch of the model filter for the change form.

        Immediately store an existing model filter's `content_type` on the
        `request` for later use.

        :param request: The current request.
        :param object_id: ID of the model filter to get.
        :param from_field: Field to filter with `object_id`.
        :return: The model filter, if found.
        """
        model_filter = super().get_object(request, object_id, from_field=from_field)
        if model_filter:
            self.set_content_type(request, model_filter.content_type)
        return model_filter

    def get_formsets_with_inlines(self, request, obj=None):
        """Add necessary parameters to inline formsets.

        Store content type on inline instance formset class for later use.
        Since the formset class is created on-the-fly with a class factory
        there should not be any conflicts or issues with thread safety
        when using a class level attribute.
        """
        for formset, inline in super().get_formsets_with_inlines(request, obj):
            formset.model_filter_content_type = self.get_content_type(request)
            yield formset, inline

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        """Create the template for the change form and update its context."""
        template = super().render_change_form(
            request, context, add=add, change=change, form_url=form_url, obj=obj
        )
        update_context(
            obj,
            template.context_data,
            self.get_content_type(request),
            self.extend_change_form_template,
            self.field_filter_inline.form,
        )
        return template

    def response_add(
        self, request: HttpRequest, obj: ModelFilter, post_url_continue=None
    ):
        """Handle the response for adding."""
        response = super().response_add(
            request, obj, post_url_continue=post_url_continue
        )
        if constants.FORM_SAVE_APPLY_DISCARD in request.POST:
            # Clear existing messages before adding new message.
            list(messages.get_messages(request))
            msg = format_html(
                _(f'The {self.opts.verbose_name} "{obj}" was applied successfully.')
            )
            self.message_user(request, msg, messages.SUCCESS)
        return self._save_apply_redirect(request, response, obj)

    def response_change(self, request: HttpRequest, obj: ModelFilter):
        """Handle the response for changing."""
        response = super().response_change(request, obj)
        return self._save_apply_redirect(request, response, obj)

    @staticmethod
    def _save_apply_redirect(
        request: HttpRequest,
        response: HttpResponse,
        model_filter: ModelFilter,
    ) -> Union[HttpResponse, HttpResponseRedirect]:
        """Generate a redirect to apply the model filter.

        Only redirect if the POST body contains the proper key.
        """
        apply_keys = [constants.FORM_SAVE_APPLY, constants.FORM_SAVE_APPLY_DISCARD]
        if any(key in request.POST for key in apply_keys):
            return HttpResponseRedirect(
                get_apply_url(model_filter.content_type, model_filter.id)
            )
        return response

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Setup the queryset for model filters."""
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.for_user(request.user)

    def get_changeform_initial_data(self, request) -> Dict:
        """Update the changeform initial data."""
        data = super().get_changeform_initial_data(request)
        data.update(dict(owner=request.user.id))
        return data

    def save_form(
        self, request: HttpRequest, form: ModelFilterForm, change: bool
    ) -> ModelFilter:
        """Update the model before it is saved."""
        model_filter = super().save_form(request, form, change)
        model_filter.owner = request.user
        model_filter.ephemeral = constants.FORM_SAVE_APPLY_DISCARD in request.POST
        return model_filter

    def has_add_permission(self, request):
        """Determine if a user can add a model filter."""
        content_type = self.get_content_type(request)
        if not content_type:
            return False
        if request.user.is_superuser:
            return True
        return user_can_access_content_type(request.user, content_type)

    def has_view_permission(
        self, request: HttpRequest, obj: Optional[ModelFilter] = None
    ) -> bool:
        """Determine if a user can view model filter admin pages."""
        permission = user_has_permission(
            request.user,
            constants.SETTING_MODEL_FILTERS_VIEW_OWNER_ONLY,
            constants.DEFAULT_MODEL_FILTERS_VIEW_OWNER_ONLY,
            model_filter=obj,
        )
        if permission is None:
            permission = super().has_view_permission(request, obj=obj)
        return permission

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[ModelFilter] = None
    ) -> bool:
        """Determine if a user can change a model filter."""
        permission = user_has_permission(
            request.user,
            constants.SETTING_MODEL_FILTERS_CHANGE_OWNER_ONLY,
            constants.DEFAULT_MODEL_FILTERS_CHANGE_OWNER_ONLY,
            model_filter=obj,
        )
        if permission is None:
            permission = super().has_change_permission(request, obj=obj)
        return permission

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[ModelFilter] = None
    ) -> bool:
        """Determine if a user can delete a model filter."""
        permission = user_has_permission(
            request.user,
            constants.SETTING_MODEL_FILTERS_DELETE_OWNER_ONLY,
            constants.DEFAULT_MODEL_FILTERS_DELETE_OWNER_ONLY,
            model_filter=obj,
        )
        if permission is None:
            permission = super().has_delete_permission(request, obj=obj)
        return permission

    def has_module_permission(self, request):
        """Determine if a user has access to the model filter app label.

        By default, all staff and above can use model filters.
        """
        if request.user.is_staff or request.user.is_superuser:
            return True
        return super().has_module_permission(request)

    @staticmethod
    def get_content_type(request: HttpRequest):
        """Get the content type stored on the request."""
        return getattr(request, "model_filter_content_type", None)

    @staticmethod
    def set_content_type(request: HttpRequest, content_type: ContentType):
        """Store a content type on the request."""
        request.model_filter_content_type = content_type


class ModelFilterAdmin(ModelFilterAdminBase, admin.ModelAdmin):
    """Manage the `ModelFilter` models with Django class level permissions."""


class GuardedModelFilterAdmin(ModelFilterAdminBase, GuardedModelAdmin):
    """Manage the `ModelFilter` models with Guardian object level permissions.

    If Guardian is not available, this falls back to class level permissions.
    """


if use_guardian():
    admin.site.register(ModelFilter, GuardedModelFilterAdmin)
else:
    admin.site.register(ModelFilter, ModelFilterAdmin)
