from django.db import migrations, models

#: Informativní poznámky, které cron a plný sync zapisují do ``note``.
#: Všechno ostatní v ``note`` jsou varování zapsaná přes ``_append_run_note`` (dnes ``_append_run_warning``).
INFORMATIVNI = {"no_changes (404)", "not_published_yet (404)", "no_changes_nepotvrzeno (404)"}


def _je_informativni(radek):
    """
    Rozhodne, jestli je řádek poznámky čistě informativní.

    :param radek: Jeden řádek pole ``note``.
    :return: ``True`` pro informativní řádek, ``False`` pro varování.
    """
    return radek in INFORMATIVNI or radek.startswith("uzsz=")


def presun_varovani(apps, schema_editor):
    """
    Přesune varování z ``note`` do nového pole ``warnings``.

    Informativní řádky zůstanou v ``note``.

    :param apps: Registr historických modelů.
    :param schema_editor: Editor schématu (nepoužívá se).
    """
    RuianSyncRun = apps.get_model("heslar", "RuianSyncRun")
    for run in RuianSyncRun.objects.exclude(note="").only("pk", "note"):
        radky = [r for r in run.note.splitlines() if r.strip()]
        info = [r for r in radky if _je_informativni(r)]
        varovani = [r for r in radky if not _je_informativni(r)]
        if varovani:
            RuianSyncRun.objects.filter(pk=run.pk).update(note="\n".join(info), warnings="\n".join(varovani))


def vrat_varovani(apps, schema_editor):
    """
    Vrátí varování zpět na konec ``note``.

    :param apps: Registr historických modelů.
    :param schema_editor: Editor schématu (nepoužívá se).
    """
    RuianSyncRun = apps.get_model("heslar", "RuianSyncRun")
    for run in RuianSyncRun.objects.exclude(warnings="").only("pk", "note", "warnings"):
        note = "\n".join(r for r in (run.note, run.warnings) if r)
        RuianSyncRun.objects.filter(pk=run.pk).update(note=note)


class Migration(migrations.Migration):

    dependencies = [
        ("heslar", "0015_alter_model_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="ruiansyncrun",
            name="warnings",
            field=models.TextField(
                blank=True, db_default="", default="", verbose_name="heslar.models.RuianSyncRun.warnings"
            ),
        ),
        migrations.RunPython(presun_varovani, vrat_varovani),
    ]
