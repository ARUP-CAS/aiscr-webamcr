# Ruční migrace pro #3421 – přejmenování modelu a tabulky vazby typ/materiál
# a odstranění atributu řady. Zachovává existující záznamy (nejde o create + delete).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("heslar", "0011_ruiankraj_email"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="HeslarDokumentTypMaterialRada",
            new_name="HeslarDokumentTypMaterial",
        ),
        migrations.AlterModelOptions(
            name="heslardokumenttypmaterial",
            options={"verbose_name_plural": "Heslář dokument typ materiál"},
        ),
        migrations.AlterModelTable(
            name="heslardokumenttypmaterial",
            table="heslar_dokument_typ_material",
        ),
        migrations.RemoveField(
            model_name="heslardokumenttypmaterial",
            name="dokument_rada",
        ),
        migrations.AlterField(
            model_name="heslardokumenttypmaterial",
            name="dokument_typ",
            field=models.ForeignKey(
                db_column="dokument_typ",
                limit_choices_to={"nazev_heslare": 35},
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="typ",
                to="heslar.heslar",
                verbose_name="heslar.models.HeslarDokumentTypMaterial.dokument_typ",
            ),
        ),
        migrations.AlterField(
            model_name="heslardokumenttypmaterial",
            name="dokument_material",
            field=models.ForeignKey(
                db_column="dokument_material",
                limit_choices_to={"nazev_heslare": 12},
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="material",
                to="heslar.heslar",
                verbose_name="heslar.models.HeslarDokumentTypMaterial.dokument_material",
            ),
        ),
    ]
