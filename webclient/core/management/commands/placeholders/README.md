# Placeholder soubory (statická sada)

Hotové, **plně funkční** minimální soubory pro každý podporovaný mimetype + katalog
`placeholder_manifest.json` (mimetype → soubor, se zaznamenaným `sha512`/`size`).

Tuto sadu používá Django příkaz `generate_metadata_fast` (viz
`webclient/core/management/commands/generate_metadata_fast.py`, issue #3967) -
hromadné generování Fedora repozitáře z DB, kdy se obsah souborů nahradí placeholderem
podle mimetype místo kopírování skutečných dat. Cesta k manifestu je v tomto příkazu
napevno (`_PLACEHOLDER_MANIFEST_PATH`, tento adresář vedle `generate_metadata_fast.py`).

`sha512` v manifestu je jen **informativní/kontrolní hodnota** - `generate_metadata_fast`
si při načtení (`_load_placeholders`) hash vždy přepočítá ze skutečně přečtených bajtů a
neshodu jen zaloguje jako WARNING (nespadne). Nespoléhej tedy na to, že hash v manifestu
je aktuální, pokud jsi soubor upravoval na jiném stroji/checkoutu - `.gitattributes`
normalizuje konce řádků textových placeholderů (`.csv`/`.txt`), takže se bajty na disku
mezi Windows a Linux checkoutem mohou lišit i beze změny obsahu.

Volitelný přepínač `--aktualizovat-db` příkazu `generate_metadata_fast` po zápisu
placeholderu přepíše `Soubor.sha_512`/`size_mb` v DB na hodnoty odpovídající vloženému
placeholderu (jinak zůstanou ukazovat na původní, skutečný soubor, který ve Fedoře po
migraci není).

Sada je statická a verzovaná v gitu; **negeneruje se za běhu**. Mimetypy odpovídají
`Soubor.get_file_extension_by_mime()` (+ alias `text/rtf`).

Provenience (jak byly soubory jednorázově vyrobeny):

- png, jpeg, gif, bmp, tiff, svg, txt, csv, pdf, rtf, zip, OOXML docx/xlsx, ODF odt/ods
  — sestaveny programově (Python stdlib + 1×1 rastry).
- `*.heic`/`*.heif` — pillow-heif; `*.rar` — WinRAR; `*.7z` — py7zr; `*.xls` — xlwt;
  `*.doc` — MS Word (uloženo jako Word 97-2003).

Pokud bys potřeboval sadu změnit (nový mimetype, jiný obsah), nahraď příslušný soubor
a **přepočítej `placeholder_manifest.json`** (sha512 + size) - `generate_metadata_fast`
sice hash při načtení přepočítá sám (viz výše), ale zastaralá hodnota v manifestu pak
zbytečně loguje WARNING při každém běhu.

## Náhledy (thumb / thumb-large)

Ke každému `orig` placeholderu existuje i dvojice předgenerovaných náhledů
(`*_thumb.png` 100×100, `*_thumb_large.png` 800×800), uložených v manifestu pod klíči
`thumb`/`thumb_large` (stejná struktura `file`/`sha512`/`size`). Používá je
`generate_metadata_fast` (viz `webclient/core/management/commands/`) při vkládání
placeholder souborů do Fedory, aby zachoval stejnou strukturu zdrojů (`orig` + `thumb`
+ `thumb-large`) jako u reálných souborů — **negenerují se za běhu**.

Vyrobeny jednorázově zavoláním produkční náhledovací logiky
(`FedoraRepositoryConnector.__generate_thumb`) nad každým `orig` placeholderem — tedy
identickým postupem, jakým by Fedora náhled vytvořila pro skutečný soubor daného typu
(reálný resize pro rastrové formáty, ikona podle mimetype pro ostatní). U `image/heic`
a `image/heif` se lokálně nepodařilo `libmagic` detekovat obsah jako obrázek (placeholder
je rozpoznán jako `application/octet-stream`), takže pro tyto dva mimetypy náhled
neexistuje (`thumb`/`thumb_large` jsou v manifestu `null`) — stejné chování jako by
nastalo u reálného HEIC/HEIF souboru, který `libmagic` nerozpozná.

`placeholder_11.bmp` byl oproti ostatním rastrovým placeholderům úmyslně zvětšen ze
zavádějícího 1×1 pixelu na 100×100 (bílý), aby otevřený soubor nepůsobil jako chyba.
