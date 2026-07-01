from django.db import migrations

# Typy notifikací, u nichž je dotčený záznam totožný s příjemcem (uloženým ``user`` FK),
# takže lze ``zaznam_ident_cely`` bezpečně doplnit zpětně z ``user.ident_cely``.
SAFE_TYPES = ["E-U-01", "E-U-02", "E-U-03", "E-U-06"]


def backfill_zaznam_ident_cely(apps, schema_editor):
    """
    Zpětně doplní ``zaznam_ident_cely`` u historických záznamů logu notifikací.

    Pouze pro typy ze :data:`SAFE_TYPES`, kde je dotčený záznam shodný s příjemcem,
    a jen tam, kde je ``user`` vyplněný a pole dosud prázdné (migrace je idempotentní).

    :param apps: Registr historických modelů poskytnutý migračním frameworkem.
    :param schema_editor: Editor schématu pro aktuální databázové spojení.
    """
    NotificationsLog = apps.get_model("uzivatel", "NotificationsLog")
    qs = NotificationsLog.objects.filter(
        notification_type__ident_cely__in=SAFE_TYPES,
        zaznam_ident_cely__isnull=True,
        user__isnull=False,
    ).select_related("user")
    batch = []
    for log in qs.iterator():
        log.zaznam_ident_cely = log.user.ident_cely
        batch.append(log)
        if len(batch) >= 1000:
            NotificationsLog.objects.bulk_update(batch, ["zaznam_ident_cely"])
            batch = []
    if batch:
        NotificationsLog.objects.bulk_update(batch, ["zaznam_ident_cely"])


class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0033_notificationslog_zaznam_ident_cely"),
    ]

    operations = [
        migrations.RunPython(backfill_zaznam_ident_cely, migrations.RunPython.noop),
    ]
