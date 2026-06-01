# Fedora OCFL shrink — migrace dat na test server (issue #3967)

Nástroj pro migraci DB + Fedory z produkce (z **běžné zálohy**, ne z živé produkce)
na test server, s možností nahradit velké binární datové soubory (`orig`) v OCFL
malými **placeholdery podle mimetype**. Tím se výrazně zmenší obsazené místo na testu.

Při náhradě se udržuje OCFL konzistentní a aktualizuje se hash jak ve Fedoře
(OCFL `inventory.json` + interní hlavička `.fcrepo/.../orig.json`), tak v DB
(`soubor.sha_512`). **XML metadata a náhledy (`thumb`, `thumb-large`) se nemění.**
Index Fedory se nepřenáší — vygeneruje se nově při startu jako ověření.

## Komponenty

| Soubor | Běží kde | Účel |
|--------|----------|------|
| `placeholders/` | — | Statická sada hotových placeholder souborů + `placeholder_manifest.json` (napevno sha512+size) |
| `ocfl_path.py` | — | Enumerace objektů (3úrovňový sestup) + deterministická cesta (sha256 n-tuple) |
| `ocfl_object.py` | — | Per-objekt náhrada **všech** `orig` (všechny verze) + přepis `inventory.json` a hlaviček |
| `fedora_db_objects.py` | storage box | Export seznamu objektů s binárkou z Fedora indexu (pro `--objects`) |
| `ocfl_shrink.py` | storage box | Paralelní, resumovatelná in-place orchestrace nad OCFL |
| `core/management/commands/shrink_soubor_hashes.py` | Django | Hromadný update `soubor.sha_512` aktuálních souborů |

Samostatný OCFL nástroj se **k databázi nepřipojuje** — pracuje jen s filesystémem
a placeholdery. Django příkaz dělá jen update `soubor.sha_512` přes nakonfigurované
Django `DATABASES` (Docker secret `/run/secrets/db_conf`, lokálně
`--settings=webclient.settings.local_settings`).

## Jak se vybírají objekty a co se zmenšuje

Klíčové: **uvnitř každého navštíveného objektu se vždy zpracují VŠECHNY orig bloby
všech verzí** (aktuální + soft-smazané + historické nahrazené). Mimetype se bere
z OCFL hlavičky `.fcrepo/.../orig.json` (párováno podle digestu), takže pro samotné
zmenšení není potřeba žádná DB.

Liší se jen **jak se vybere množina objektů**:

1. **`--objects objects.txt` (doporučeno pro produkci):** seznam `object_id`
   vytažený z Fedora indexu (objekty s aspoň jednou živou binárkou). Navštíví jen
   tyto objekty (ne plošně celý OCFL) → rychlé. Uvnitř zmenší všechny verze.
   Vynechá jen objekty bez živé binárky (plně **tombstonované** smazané) — ty nás
   nezajímají a v indexu nejsou.
2. **plošný sken (bez `--objects`):** projde úplně všechny OCFL objekty (sestup
   3 úrovně hex-tuple, ne `os.walk`/stat storm). Zachytí i tombstonované. Pomalejší
   (čte i objekty bez binárek), ale nezávislé na DB a kompletní.

Proč se objekty berou z Fedora indexu, ne z Django DB / ne plošně:
- **Django DB** (`soubor`) nezná soft-smazané ani smazané záznamy.
- **Fedora index** (`simple_search` + `ocfl_id_map`) zná všechny **živé** zdroje
  (vč. soft-smazaných s příznakem) → výpis objektů s binárkou. Staré nahrazené verze
  v indexu nejsou, ale to nevadí: jejich objekt je v indexu díky aktuální binárce a
  zmenšení uvnitř objektu jede přes **OCFL manifest** (všechny verze).
- Ověřeno na datech: 8 objektů s orig na disku, 6 v indexu; 2 mimo index byly plně
  tombstonované (`containment.end_time`) — mimo rozsah.

## Runbook (in-place)

```bash
# 1) Přenos DB z produkce na test — RUČNĚ (backup → restore), mimo tento nástroj.

# 2) Přenos OCFL zálohy na test storage KOPIÍ PO BLOCÍCH (block-level: image/snapshot
#    svazku, dd, LVM/FS snapshot) — Fedora má spoustu malých souborů, blok je rychlejší.

# 3) Nakopírovat statickou sadu placeholderů (verzovaná v repu) do /home/migrace,
#    které je do web kontejneru mountnuté jako /vol/data-migrace (viz docker-compose.yml)
#    — pak ji krok 7 přečte uvnitř kontejneru bez dalšího kopírování.
cp -r scripts/fedora_ocfl_shrink/placeholders /home/migrace/placeholders

# 4a) Seznam objektů s binárkou z Fedora indexu (helper, nebo ekvivalentní SQL níže)
python3 scripts/fedora_ocfl_shrink/fedora_db_objects.py \
    --host <fcrepo-db-host> --port 5432 --dbname fcrepo --user fcrepo \
    --password ****** --out /tmp/objects.txt

# 4b) In-place zmenšení OCFL nad těmito objekty (uvnitř všechny verze).
#     Nejdřív vyzkoušet --dry-run na vzorku.
python3 scripts/fedora_ocfl_shrink/ocfl_shrink.py \
    --ocfl-root /opt/fcrepo/fcrepo-home/data/ocfl-root \
    --objects /tmp/objects.txt \
    --placeholders /home/migrace/placeholders \
    --done-log /tmp/ocfl_done.log \
    --report-json /tmp/ocfl_report.json \
    --workers 8
# (Alternativa bez DB: vynechat --objects = plošný sken celého OCFL, zachytí i tombstony.)

# 5) Vyprázdnit fcrepo index DB (nebo -Dfcrepo.rebuild.on.start=true);
#    rebuild fixity/objects validation nechat default (false).

# 6) Start Fedory nad upraveným OCFL → rebuild indexu z OCFL (funkční ověření).

# 7) Nasadit test (stack běží) a NAKONEC hromadný update hashů v DB (jen aktuální
#    soubory — víc Django DB nezná). Spustit v běžícím web kontejneru s production settings.
#    Manifest je z /home/migrace vidět uvnitř kontejneru jako /vol/data-migrace.
sudo docker exec -it $(sudo docker ps -q -f name=swarm_webamcr_web) \
    python3 manage.py shrink_soubor_hashes \
    --placeholder-manifest /vol/data-migrace/placeholders/placeholder_manifest.json \
    --settings=webclient.settings.production
```

Ekvivalentní SQL pro krok 4a (psql, bez psycopg2):

```sql
\copy (
  SELECT DISTINCT m.ocfl_id
  FROM simple_search s
  JOIN ocfl_id_map m ON m.fedora_id = s.fedora_id
  WHERE s.fedora_id LIKE '%/file/%/orig'
  ORDER BY m.ocfl_id
) TO '/tmp/objects.txt'
```

> Pozn.: DB update (krok 7) se týká jen aktuálních souborů (řádky `soubor` s `/file/`).
> Soft-smazané a historické verze nemají v Django DB záznam, takže se v DB neaktualizují —
> jejich hash je opravený jen v OCFL (a to je správně, jiný zdroj pravdy pro ně není).

## Ověření

- **OCFL validace:** `rocfl validate` / `ocfl-validate` na vzorku a na dotčených
  víceverzových objektech.
- **Rebuild Fedory** (krok 6) projde = indexovatelnost OK.
- **Parita DB ↔ manifest:** `manage.py shrink_soubor_hashes --placeholder-manifest … --verify`.
- **Reconciliace:** porovnat `replaced_by_mimetype` z `ocfl_report.json` s počty v DB.

## Idempotence a resumování

- `ocfl_shrink.py` je idempotentní (objekt, kde už `orig` digest == placeholder digest,
  přeskočí) a resumovatelný přes `--done-log`.
- Zápisy jsou atomické (dočasný soubor + `os.replace`).

## Placeholdery a validita

Placeholdery jsou **statická, verzovaná sada** v [`placeholders/`](placeholders/README.md)
— hotové, **plně funkční** soubory svého typu (otevřou se v dané aplikaci) + manifest
s **napevno uloženými** `sha512` a `size`. **Negenerují se za běhu.** `ocfl_shrink.py`
při startu ověří, že sha512 i velikost každého souboru odpovídají manifestu.

Provenience souborů viz [`placeholders/README.md`](placeholders/README.md). Mimetype,
který v manifestu chybí, OCFL nástroj přeskočí (ponechá originál) a vykáže ho
v `skipped_no_placeholder`.
