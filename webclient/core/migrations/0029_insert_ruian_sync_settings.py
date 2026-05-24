"""
Vloží default konfiguraci stahování RÚIAN VFR souborů do ``CustomAdminSettings``.

Záznam je čten z :mod:`heslar.ruian_sync.vfr_download` – konkrétní URL,
``prefer_atom`` přepínač i cílový adresář (``target_dir``) jsou tedy
dynamicky upravitelné v admin rozhraní bez restartu workeru.

Hodnoty kopírují modulové defaulty (``_DEFAULTS``); pokud DB záznam
v budoucnu chybí, modul stále funguje (fallback na hardkódované defaulty).
"""

import json

from django.db import migrations


_GROUP = "ruian_sync"
_ITEM = "vfr_download"
_VALUE = {
    "base_url": "https://vdp.cuzk.gov.cz/vymenny_format/soucasna/",
    "atom_feed_url": "https://atom.cuzk.gov.cz/RUIAN-S-K-Z/RUIAN-S-K-Z.xml",
    "prefer_atom": False,
    "target_dir": "/vol/data-migrace/ruian_delta/",
}


def insert_ruian_sync_settings(apps, schema_editor):
    """
    Vloží řádek ``(item_group='ruian_sync', item_id='vfr_download')``
    s default JSON konfigurací stahování.

    Používá ``apps.get_model`` (historická verze modelu), aby migrace
    nezávisela na aktuálním stavu třídy ``CustomAdminSettings`` v kódu.

    :param apps: Standardní parametr Django datové migrace – přístup
        k historickému stavu modelů.
    :param schema_editor: Standardní parametr Django datové migrace.
    """
    CustomAdminSettings = apps.get_model("core", "CustomAdminSettings")
    CustomAdminSettings.objects.update_or_create(
        item_group=_GROUP,
        item_id=_ITEM,
        defaults={"value": json.dumps(_VALUE, indent=4)},
    )


def remove_ruian_sync_settings(apps, schema_editor):
    """
    Reverzní operace – odstraní record při downgrade migrace.

    :param apps: Standardní parametr Django datové migrace.
    :param schema_editor: Standardní parametr Django datové migrace.
    """
    CustomAdminSettings = apps.get_model("core", "CustomAdminSettings")
    CustomAdminSettings.objects.filter(item_group=_GROUP, item_id=_ITEM).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_remove_apirequestlog"),
    ]

    operations = [
        migrations.RunPython(insert_ruian_sync_settings, remove_ruian_sync_settings),
    ]
