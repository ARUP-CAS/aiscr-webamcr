## Návrhy na zlepšení promptu pro T10 (skripty)

- V sekci SCRIPTS ANALYSIS (T10) explicitně uvést, že konfigurační soubory (`crontab.txt`, `uwsgi_site.ini`) se neanalyzují řádek po řádku jako spustitelné skripty, ale že agent zdokumentuje jejich vztah ke skriptům (co spouštějí, jak často) a případná rizika (chybějící logování nebo error handling v volaných příkazech).
- Upřesnit rozsah: skripty v `docs/` (generátory dokumentace, např. `generate_module_docs.py`, `convert_to_rst.py`) spadají do T08; do T10 patří pouze obsah adresáře `scripts/` v kořeni repozitáře.
- Doplnit příklad struktury položky v `issues` v `scripts_analysis.json`: `id`, `severity`, `summary`, `scripts` (pole cest), `recommendation`, aby byl výstup konzistentní mezi agenty.
- Připomenout, že u shell skriptů má agent vždy zkontrolovat přítomnost `set -e` / `set -u` / `set -o pipefail` a u skriptů, které volají destruktivní operace (DROP DATABASE, rm -rf, přepsání souborů), ověření povinných proměnných prostředí nebo argumentů.
