from django.db import migrations


class Migration(migrations.Migration):
    """Přesun modelu ``ApiRequestLog`` z aplikace ``core`` do aplikace ``api``.

    Provedeno jako ``SeparateDatabaseAndState`` — pouze úprava stavu Django ORM,
    DB tabulka ``api_log_pozadavku`` zůstává beze změny.
    """

    dependencies = [
        ("core", "0027_alter_permissions_action_spoluprace_edit_projekty"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="ApiRequestLog"),
            ],
            database_operations=[],
        ),
    ]
