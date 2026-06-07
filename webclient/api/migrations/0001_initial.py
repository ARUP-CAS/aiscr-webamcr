import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Inicializace aplikace ``api`` — převzetí modelu ``ApiRequestLog`` z aplikace ``core``.

    Provedeno jako ``SeparateDatabaseAndState`` — pouze úprava stavu Django ORM,
    DB tabulka ``api_log_pozadavku`` zůstává beze změny.
    """

    initial = True

    dependencies = [
        ("core", "0028_remove_apirequestlog"),
        ("pas", "0011_alter_samostatnynalez_projekt"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="ApiRequestLog",
                    fields=[
                        ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("client_ip", models.GenericIPAddressField(verbose_name="api.model.apiRequestLog.clientIp")),
                        ("received_at", models.DateTimeField(auto_now_add=True, verbose_name="api.model.apiRequestLog.receivedAt")),
                        ("finished_at", models.DateTimeField(blank=True, null=True, verbose_name="api.model.apiRequestLog.finishedAt")),
                        ("request_target", models.CharField(choices=[("samostatny_nalez_xml_import", "api.model.apiRequestLog.requestTarget.samostatnyNalezXmlImport"), ("samostatny_nalez_evidencni_cislo_patch", "api.model.apiRequestLog.requestTarget.samostatnyNalezEvidencniCisloPatch"), ("samostatny_nalez_fotografie_upload", "api.model.apiRequestLog.requestTarget.samostatnyNalezFotografieUpload")], max_length=64, verbose_name="api.model.apiRequestLog.requestTarget")),
                        ("filename", models.CharField(blank=True, max_length=255, null=True, verbose_name="api.model.apiRequestLog.filename")),
                        ("file_size", models.PositiveIntegerField(blank=True, null=True, verbose_name="api.model.apiRequestLog.fileSize")),
                        ("status", models.CharField(choices=[("received", "api.model.apiRequestLog.status.received"), ("processing", "api.model.apiRequestLog.status.processing"), ("success", "api.model.apiRequestLog.status.success"), ("failure", "api.model.apiRequestLog.status.failure")], default="received", max_length=16, verbose_name="api.model.apiRequestLog.status")),
                        ("ident_cely", models.CharField(blank=True, max_length=64, null=True, verbose_name="api.model.apiRequestLog.identCely")),
                        ("errors", models.JSONField(blank=True, null=True, verbose_name="api.model.apiRequestLog.errors")),
                        ("samostatny_nalez", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="pas.samostatnynalez", verbose_name="api.model.apiRequestLog.samostatnyNalez")),
                        ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name="api.model.apiRequestLog.user")),
                    ],
                    options={
                        "verbose_name": "api.model.apiRequestLog.modelTitle.label",
                        "verbose_name_plural": "api.model.apiRequestLog.modelTitles.label",
                        "db_table": "api_log_pozadavku",
                        "ordering": ["-received_at"],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
