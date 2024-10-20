# Generated by Django 4.2.3 on 2023-09-22 06:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("core", "0012_customadminsettings_alter_odstavkasystemu_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="soubor",
            options={"ordering": ["nazev"]},
        ),
        migrations.CreateModel(
            name="Permissions",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "address_in_app",
                    models.CharField(
                        max_length=150,
                        verbose_name="core.models.permissions.addressInApp",
                    ),
                ),
                (
                    "base",
                    models.BooleanField(
                        default=True, verbose_name="core.models.permissions.base"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        max_length=10,
                        null=True,
                        verbose_name="core.models.permissions.status",
                    ),
                ),
                (
                    "ownership",
                    models.CharField(
                        choices=[
                            ("my", "core.models.permissions.ownershipChoices.my"),
                            ("our", "core.models.permissions.ownershipChoices.our"),
                        ],
                        max_length=10,
                        null=True,
                        verbose_name="core.models.permissions.ownership",
                    ),
                ),
                (
                    "accessibility",
                    models.CharField(
                        choices=[
                            ("my", "core.models.permissions.ownershipChoices.my"),
                            ("our", "core.models.permissions.ownershipChoices.our"),
                        ],
                        max_length=10,
                        null=True,
                        verbose_name="core.models.permissions.accessibility",
                    ),
                ),
                (
                    "main_role",
                    models.ForeignKey(
                        db_column="role",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="role_opravneni",
                        to="auth.group",
                        verbose_name="core.models.permissions.mainRole",
                    ),
                ),
            ],
            options={
                "verbose_name": "core.model.permissions.modelTitle.label",
                "verbose_name_plural": "core.model.permissions.modelTitles.label",
            },
        ),
    ]
