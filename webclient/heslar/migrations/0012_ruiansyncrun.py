# Generated for issue #372 (aktualizace katastrů podle RÚIAN)
#
# Sloučená migrace pro `RuianSyncRun`. Drží finální podobu tabulky:
# variant a affected_neident_akce jsou zde zařazeny rovnou (dříve postupně
# přes 0013_ruiansyncrun_variant.py a 0014_ruiansyncrun_affected_neident_akce.py;
# obě byly před nasazením sloučeny do tohoto souboru).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("heslar", "0011_ruiankraj_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="RuianSyncRun",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "started_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="heslar.models.RuianSyncRun.started_at"
                    ),
                ),
                (
                    "finished_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="heslar.models.RuianSyncRun.finished_at"
                    ),
                ),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("full", "heslar.models.RuianSyncRun.mode.full"),
                            ("delta", "heslar.models.RuianSyncRun.mode.delta"),
                        ],
                        db_index=True,
                        max_length=8,
                        verbose_name="heslar.models.RuianSyncRun.mode",
                    ),
                ),
                ("source", models.CharField(max_length=64, verbose_name="heslar.models.RuianSyncRun.source")),
                (
                    "triggered_by",
                    models.CharField(
                        choices=[
                            ("manage", "heslar.models.RuianSyncRun.triggered_by.manage"),
                            ("cron", "heslar.models.RuianSyncRun.triggered_by.cron"),
                            ("admin", "heslar.models.RuianSyncRun.triggered_by.admin"),
                        ],
                        db_index=True,
                        max_length=8,
                        verbose_name="heslar.models.RuianSyncRun.triggered_by",
                    ),
                ),
                (
                    "source_path",
                    models.TextField(blank=True, default="", verbose_name="heslar.models.RuianSyncRun.source_path"),
                ),
                (
                    "data_valid_to",
                    models.DateField(db_index=True, verbose_name="heslar.models.RuianSyncRun.data_valid_to"),
                ),
                (
                    "since",
                    models.DateField(blank=True, null=True, verbose_name="heslar.models.RuianSyncRun.since"),
                ),
                (
                    "variant",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=8,
                        verbose_name="heslar.models.RuianSyncRun.variant",
                    ),
                ),
                (
                    "kraj_upserts",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.kraj_upserts"),
                ),
                (
                    "kraj_deletes",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.kraj_deletes"),
                ),
                (
                    "okres_upserts",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.okres_upserts"),
                ),
                (
                    "okres_deletes",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.okres_deletes"),
                ),
                (
                    "katastr_upserts",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.katastr_upserts"),
                ),
                (
                    "katastr_deletes",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.katastr_deletes"),
                ),
                (
                    "affected_az",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.affected_az"),
                ),
                (
                    "affected_projekt",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.affected_projekt"),
                ),
                (
                    "affected_sn",
                    models.IntegerField(default=0, verbose_name="heslar.models.RuianSyncRun.affected_sn"),
                ),
                (
                    "affected_neident_akce",
                    models.IntegerField(
                        default=0, verbose_name="heslar.models.RuianSyncRun.affected_neident_akce"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "heslar.models.RuianSyncRun.status.running"),
                            ("success", "heslar.models.RuianSyncRun.status.success"),
                            ("failed", "heslar.models.RuianSyncRun.status.failed"),
                        ],
                        db_index=True,
                        default="running",
                        max_length=8,
                        verbose_name="heslar.models.RuianSyncRun.status",
                    ),
                ),
                ("error", models.TextField(blank=True, default="", verbose_name="heslar.models.RuianSyncRun.error")),
                ("note", models.TextField(blank=True, default="", verbose_name="heslar.models.RuianSyncRun.note")),
            ],
            options={
                "verbose_name": "Záznam synchronizace RÚIAN",
                "verbose_name_plural": "Záznamy synchronizace RÚIAN",
                "db_table": "ruian_sync_run",
                "ordering": ["-started_at"],
            },
        ),
    ]
