import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ModelFilter",
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
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="A name for the model filter.",
                        max_length=1024,
                        null=True,
                        verbose_name="name",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="An optional description of the model filter.",
                        null=True,
                        verbose_name="description",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="The date and time the model filter was created.",
                        verbose_name="created",
                    ),
                ),
                (
                    "ephemeral",
                    models.BooleanField(
                        default=False,
                        help_text="A one-off model filter that is deleted after initial use.",
                        verbose_name="ephemeral",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        help_text="The model being filtered.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                        verbose_name="content type",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        help_text="The user that created, and owns, the model filter.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="model_filters",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="owner",
                    ),
                ),
            ],
            options={
                "verbose_name": "model filter",
                "verbose_name_plural": "model filters",
            },
        ),
        migrations.CreateModel(
            name="FieldFilter",
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
                (
                    "field",
                    models.TextField(
                        help_text="The path to the field to filter.",
                        verbose_name="field",
                    ),
                ),
                (
                    "operator",
                    models.CharField(
                        help_text="The operator to use for the field value.",
                        max_length=1024,
                        verbose_name="operator",
                    ),
                ),
                (
                    "value",
                    models.TextField(
                        help_text="The value to filter the field with.",
                        verbose_name="value",
                    ),
                ),
                (
                    "negate",
                    models.BooleanField(
                        default=False,
                        help_text="Negate the query filter.",
                        verbose_name="negate",
                    ),
                ),
                (
                    "model_filter",
                    models.ForeignKey(
                        help_text="The model filter that the field filter belongs to.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fields",
                        to="model_filters.modelfilter",
                        verbose_name="model filter",
                    ),
                ),
            ],
            options={
                "verbose_name": "field filter",
                "verbose_name_plural": "field filters",
                "ordering": ("id",),
            },
        ),
        migrations.AddIndex(
            model_name="modelfilter",
            index=models.Index(fields=["name"], name="model_filte_name_cac84f_idx"),
        ),
        migrations.AddIndex(
            model_name="modelfilter",
            index=models.Index(
                fields=["-created"], name="model_filte_created_4e300f_idx"
            ),
        ),
    ]
