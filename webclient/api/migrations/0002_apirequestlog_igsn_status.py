from django.db import migrations, models


class Migration(migrations.Migration):
    """Přidá pole ``igsn_status`` do ``ApiRequestLog`` pro audit výsledku aktualizace IGSN (#4523)."""

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="apirequestlog",
            name="igsn_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("retry_pending", "api.model.apiRequestLog.igsnStatus.retryPending"),
                    ("updated", "api.model.apiRequestLog.igsnStatus.updated"),
                    ("failed", "api.model.apiRequestLog.igsnStatus.failed"),
                ],
                max_length=20,
                null=True,
                verbose_name="api.model.apiRequestLog.igsnStatus",
            ),
        ),
    ]
