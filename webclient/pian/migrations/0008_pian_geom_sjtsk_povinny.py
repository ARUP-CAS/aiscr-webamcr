# Schémová migrace: ``Pian.geom_sjtsk`` se stává povinným (``NOT NULL``),
# stejně jako ``Pian.geom``.
#
# PIAN z principu leží na území ČR, takže JTSK protějšek dává smysl vždy.
# Dokud byl sloupec nullable, procházely DB záznamy bez JTSK a spatial
# dotazy určující katastr (``core.utils.get_all_pians_with_akce`` →
# ``ST_Intersects`` proti ``ruian_katastr.hranice``, od migrace
# ``heslar.0013`` v EPSG:5514) na nich vracely ``NULL``. Katastr se
# nedohledal a připojení pianu k archeologickému záznamu jeho
# ``hlavni_katastr`` tiše neaktualizovalo.
#
# Zároveň se zjednodušuje ``CheckConstraint`` ``pian_geom_check``: původní
# podmínka explicitně povolovala chybějící JTSK u ``geom_system='4326'``,
# což si s novým ``NOT NULL`` odporuje. Její třetí větev (obojí ``NULL``)
# je nadále nesplnitelná a zbylé dvě vždy pravdivé, takže zůstává jen to,
# co má reálnou vypovídací hodnotu – výčet povolených hodnot
# ``geom_system``.

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pian", "0007_remove_pian_geom_sjtsk_updated_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pian",
            name="geom_sjtsk",
            field=django.contrib.gis.db.models.fields.GeometryField(db_index=True, srid=5514),
        ),
        migrations.RemoveConstraint(
            model_name="pian",
            name="pian_geom_check",
        ),
        migrations.AddConstraint(
            model_name="pian",
            constraint=models.CheckConstraint(
                condition=models.Q(("geom_system__in", ["4326", "5514"])),
                name="pian_geom_check",
            ),
        ),
    ]
