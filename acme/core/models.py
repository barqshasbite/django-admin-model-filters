# coding=utf-8

"""Application models."""

from django.db import models


class Product(models.Model):
    """An ACME product."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    width = models.DecimalField(max_digits=8, decimal_places=2)
    height = models.DecimalField(max_digits=8, decimal_places=2)
    depth = models.DecimalField(max_digits=8, decimal_places=2)
    weight = models.FloatField()
    min_age = models.PositiveSmallIntegerField(default=18)
    invented = models.DateField()
    released = models.DateTimeField()
    flammable = models.BooleanField(default=False)
    explosive = models.BooleanField(null=True, default=False)
    serial_number = models.UUIDField(unique=True)
    parts = models.ManyToManyField("core.Part", blank=True)

    def __str__(self):
        return self.name


class Part(models.Model):
    """An ACME part."""

    MATERIAL_WOOD = "wood"
    MATERIAL_STEEL = "steel"
    MATERIAL_UNOBTAINIUM = "unobtainium"
    MATERIALS = [
        (1, MATERIAL_WOOD),
        (2, MATERIAL_STEEL),
        (3, MATERIAL_UNOBTAINIUM),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    part_number = models.CharField(max_length=100, unique=True)
    material = models.IntegerField(choices=MATERIALS)
    version = models.PositiveIntegerField(default=1)
    weight = models.FloatField()

    def __str__(self):
        return self.name


class Customer(models.Model):
    """An ACME customer."""

    MEMBERSHIP_REGULAR = "regular"
    MEMBERSHIP_SILVER = "silver"
    MEMBERSHIP_GOLD = "gold"
    MEMBERSHIP_PLATINUM = "platinum"
    MEMBERSHIPS = [
        (MEMBERSHIP_REGULAR, "Regular"),
        (MEMBERSHIP_SILVER, "Silver"),
        (MEMBERSHIP_GOLD, "Gold"),
        (MEMBERSHIP_PLATINUM, "Platinum"),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    first_seen = models.DateTimeField(auto_now_add=True)
    membership = models.CharField(max_length=100, choices=MEMBERSHIPS)

    def __str__(self):
        return self.name


class Purchase(models.Model):
    """An ACME purchase order."""

    customer = models.ForeignKey("core.Customer", on_delete=models.PROTECT)
    product = models.ForeignKey("core.Product", on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    total = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.customer.name})"
