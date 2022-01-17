import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
                ("first_seen", models.DateTimeField(auto_now_add=True)),
                (
                    "membership",
                    models.CharField(
                        choices=[
                            ("regular", "Regular"),
                            ("silver", "Silver"),
                            ("gold", "Gold"),
                            ("platinum", "Platinum"),
                        ],
                        max_length=100,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Part",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("part_number", models.CharField(max_length=100, unique=True)),
                (
                    "material",
                    models.IntegerField(
                        choices=[(1, "wood"), (2, "steel"), (3, "unobtainium")]
                    ),
                ),
                ("version", models.PositiveIntegerField(default=1)),
                ("weight", models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("width", models.DecimalField(decimal_places=2, max_digits=8)),
                ("height", models.DecimalField(decimal_places=2, max_digits=8)),
                ("depth", models.DecimalField(decimal_places=2, max_digits=8)),
                ("weight", models.FloatField()),
                ("min_age", models.PositiveSmallIntegerField(default=18)),
                ("invented", models.DateField()),
                ("released", models.DateTimeField()),
                ("flammable", models.BooleanField(default=False)),
                ("explosive", models.BooleanField(null=True, default=False)),
                ("serial_number", models.UUIDField(unique=True)),
                ("parts", models.ManyToManyField(blank=True, to="core.Part")),
            ],
        ),
        migrations.CreateModel(
            name="Purchase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.IntegerField(default=1)),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("total", models.DecimalField(decimal_places=2, max_digits=8)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="core.customer"
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="core.product"
                    ),
                ),
            ],
        ),
    ]
