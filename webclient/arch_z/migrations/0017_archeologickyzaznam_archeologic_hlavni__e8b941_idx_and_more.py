# Generated by Django 4.2.8 on 2024-03-25 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("arch_z", "0016_alter_akce_je_nz_alter_akce_odlozena_nz_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="archeologickyzaznam",
            index=models.Index(
                fields=["hlavni_katastr", "ident_cely"],
                name="archeologic_hlavni__e8b941_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="archeologickyzaznam",
            index=models.Index(
                fields=["hlavni_katastr", "ident_cely", "stav"],
                name="archeologic_hlavni__e727a8_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="archeologickyzaznam",
            index=models.Index(
                fields=["hlavni_katastr", "ident_cely", "historie"],
                name="archeologic_hlavni__4861ba_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="archeologickyzaznam",
            index=models.Index(
                fields=["hlavni_katastr", "ident_cely", "historie", "stav"],
                name="archeologic_hlavni__6ead9b_idx",
            ),
        ),
    ]
