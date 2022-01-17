# coding=utf-8

"""Application administration."""

from django.contrib import admin

from acme.core.models import Customer, Part, Product, Purchase
from model_filters.admin.mixins import ModelFilterMixin


@admin.register(Product)
class ProductAdmin(ModelFilterMixin, admin.ModelAdmin):
    """Manage ACME products."""

    list_display = ["id", "name", "description"]
    list_filter = ["flammable"]
    ordering = ["name"]
    model_filter_fields = [field.name for field in Product._meta.fields] + [
        ("parts__material", "Parts Material")
    ]


@admin.register(Part)
class PartAdmin(ModelFilterMixin, admin.ModelAdmin):
    """Manage ACME parts."""

    list_display = ["id", "name", "part_number", "material"]
    list_filter = ["material"]
    ordering = ["name"]
    model_filter_fields = [field.name for field in Part._meta.fields]


@admin.register(Customer)
class CustomerAdmin(ModelFilterMixin, admin.ModelAdmin):
    """Manage ACME customers."""

    list_display = ["id", "name", "membership"]
    list_filter = ["membership"]
    ordering = ["name"]
    model_filter_fields = [field.name for field in Customer._meta.fields]


@admin.register(Purchase)
class PurchaseAdmin(ModelFilterMixin, admin.ModelAdmin):
    """Manage ACME purchases."""

    list_display = ["id", "product", "customer", "price", "quantity", "total"]
    list_filter = ["customer"]
    ordering = ["product__name"]
    model_filter_fields = [field.name for field in Purchase._meta.fields] + [
        ("product__weight", "Product Weight"),
        ("customer__membership", "Customer Membership"),
        ("product__parts__material", "Product Parts Material"),
    ]
