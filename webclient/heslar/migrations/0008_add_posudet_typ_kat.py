from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('heslar', '0007_alter_heslar_unique_together_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            INSERT INTO heslar_nazev (id,nazev)
            VALUES (51,'posudek_typ_kat')
            ON CONFLICT (id) DO NOTHING;
            """,
            reverse_sql="",
        ),
        migrations.RunSQL(
            sql="""
            INSERT INTO heslar (id,ident_cely,heslo,popis,zkratka,heslo_en,popis_en,razeni,nazev_heslare)
            VALUES 
                (1469,'HES-001491','bioarcheologie','',NULL,'bioarchaeology','',2,51),
                (1470,'HES-001492','absolutní datování','',NULL,'absolute dating','',1,51),
                (1471,'HES-001493','geoarcheologie','',NULL,'geoarchaeology','',3,51),
                (1472,'HES-001494','materiálové analýzy','',NULL,'material analysis','',4,51),
                (1473,'HES-001495','jiné expertní zpracování','',NULL,'other expert analysis','',5,51)
            ON CONFLICT (id) DO NOTHING;
            """,
            reverse_sql="",
        ),
         migrations.RunSQL(
            sql="""
            INSERT INTO heslar_hierarchie (id,typ,heslo_nadrazene,heslo_podrazene)
            VALUES 
                (1179,'podřízenost',1469,626),
                (1180,'podřízenost',1469,615),
                (1181,'podřízenost',1469,599),
                (1182,'podřízenost',1469,598),
                (1183,'podřízenost',1469,600),
                (1184,'podřízenost',1469,597),
                (1185,'podřízenost',1469,605),
                (1186,'podřízenost',1469,604),
                (1187,'podřízenost',1469,601),
                (1188,'podřízenost',1469,627),
                (1189,'podřízenost',1469,602),
                (1190,'podřízenost',1469,628),
                (1191,'podřízenost',1471,607),
                (1192,'podřízenost',1471,623),
                (1193,'podřízenost',1469,596),
                (1194,'podřízenost',1471,608),
                (1195,'podřízenost',1471,629),
                (1196,'podřízenost',1471,630),
                (1197,'podřízenost',1471,631),
                (1198,'podřízenost',1471,632),
                (1199,'podřízenost',1471,609),
                (1200,'podřízenost',1471,611),
                (1201,'podřízenost',1473,622),
                (1202,'podřízenost',1473,633),
                (1203,'podřízenost',1473,621),
                (1204,'podřízenost',1473,624),
                (1205,'podřízenost',1472,617),
                (1206,'podřízenost',1472,614),
                (1207,'podřízenost',1472,613),
                (1208,'podřízenost',1472,616),
                (1209,'podřízenost',1472,625)
            ON CONFLICT (id) DO NOTHING;
            """,
            reverse_sql="",
        ),
    ]
