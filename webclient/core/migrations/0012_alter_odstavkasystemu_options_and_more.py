# Generated by Django 4.2.3 on 2023-09-21 12:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("core", "0011_merge_0009_ident_sequences_v2_0010_alter_soubor_path"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="odstavkasystemu",
            options={
                "verbose_name": "core.model.OdstavkaSystemu.modelTitle.label",
                "verbose_name_plural": "core.model.OdstavkaSystemu.modelTitles.label",
            },
        ),
        migrations.RemoveField(
            model_name="soubor",
            name="repository_uuid",
        ),
        migrations.AlterField(
            model_name="odstavkasystemu",
            name="cas_odstavky",
            field=models.TimeField(
                verbose_name="core.model.OdstavkaSystemu.casOdstavky.label"
            ),
        ),
        migrations.AlterField(
            model_name="odstavkasystemu",
            name="datum_odstavky",
            field=models.DateField(
                verbose_name="core.model.OdstavkaSystemu.datumOdstavky.label"
            ),
        ),
        migrations.AlterField(
            model_name="odstavkasystemu",
            name="info_od",
            field=models.DateField(
                verbose_name="core.model.OdstavkaSystemu.infoOd.label"
            ),
        ),
        migrations.AlterField(
            model_name="odstavkasystemu",
            name="status",
            field=models.BooleanField(
                default=True, verbose_name="core.model.OdstavkaSystemu.status.label"
            ),
        ),
        migrations.AlterField(
            model_name="soubor",
            name="path",
            field=models.CharField(max_length=500, null=True),
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
        ),
    ]
