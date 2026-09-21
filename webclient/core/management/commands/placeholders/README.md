# Placeholder soubory (statická sada)

Hotové, **plně funkční** minimální soubory pro každý podporovaný mimetype + katalog
`placeholder_manifest.json` (mimetype → soubor, se zaznamenaným `sha512`/`size`).

Tuto sadu používá Django příkaz `generate_metadata_fast` (viz
`webclient/core/management/commands/generate_metadata_fast.py`, issue #3967) -
hromadné generování Fedora repozitáře z DB, kdy se obsah souborů nahradí placeholderem
podle mimetype místo kopírování skutečných dat. Cesta k manifestu je v tomto příkazu
napevno (`_PLACEHOLDER_MANIFEST_PATH`, tento adresář vedle `generate_metadata_fast.py`).

`sha512` v manifestu je **kontrolní hodnota** - do Fedory jde vždy hash dopočítaný ze
skutečně přečtených bajtů (`_load_placeholders`). Neshoda proti manifestu ale běh
**zastaví**: `_load_placeholders` zaloguje ERROR `placeholder_hash_mismatch` a vyhodí
`ValueError`, které `handle` převede na `CommandError` - tedy ještě předtím, než se do
Fedory cokoli zapíše. (Dřív to bylo jen varování, jenže to v logu 24hodinového běhu
zapadne, poškozené bajty ve Fedoře zůstanou nevratně a s `--aktualizovat-db` se tentýž
špatný hash uloží i do DB.) Konce řádků chrání `.gitattributes`
(`placeholders/** -text`), takže každý checkout na každé platformě dostane bajty shodné
s blobem v gitu; neshoda proto znamená zastaralý manifest nebo změněný/poškozený
placeholder.

Pozor na past, která tohle jednou už schovala (issue #3967): pokud máš working tree
vytvořený **před** opravou `.gitattributes`, git ti soubory sám nepřepíše a `git status`
mlčí, protože index má zapsanou zkonvertovanou velikost. Takový strom obsahuje
CRLF-poškozené placeholdery (u `placeholder_01.pdf` to rozbíjí `xref` offsety, tedy
neplatné PDF). Náprava: soubory smazat a `git checkout -- <cesty>`, pak ověřit, že
manifest souhlasí i proti `git cat-file -p HEAD:<cesta>`, ne jen proti disku.

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
sice hash při načtení přepočítá sám (viz výše), ale se zastaralou hodnotou v manifestu
odmítne vůbec začít. Přepočítávej z bajtů blobu (`git cat-file`) nebo
z čerstvého checkoutu, ne z working tree, u kterého si nejsi jistý normalizací.

## Náhledy (thumb / thumb-large)

Ke každému `orig` placeholderu existuje i dvojice předgenerovaných náhledů
(`*_thumb.png`, `*_thumb_large.png`), uložených v manifestu pod klíči
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

Rozměry náhledů nejsou pevné: `__generate_thumb` volá `Image.thumbnail` s hranou
`THUMB_MAX_PX`, resp. `THUMB_LARGE_MAX_PX` (`core/repository_connector.py`, dnes 100
a 800 px), a `thumbnail` obrázek **nikdy nezvětšuje** - jsou to tedy horní meze, ne cílové
rozměry. Předloha menší než mez si svůj rozměr podrží. Jediný zdroj pravdy jsou ty dvě
konstanty; `test_rozmery_nahledu_odpovidaji_generatoru_aplikace` je importuje a očekávané
rozměry dopočítá týmž `thumbnail()`, takže změna v aplikaci posune i test.

`placeholder_11.bmp` byl oproti ostatním rastrovým placeholderům úmyslně zvětšen ze
zavádějícího 1×1 pixelu na 100×100 (bílý), aby otevřený soubor nepůsobil jako chyba.
Zůstává ale u 100×100, zatímco ostatní rastry mají 300×300: BMP se neukládá komprimovaně,
takže 300×300 by znamenalo 270 kB místo 30 kB - a to na každém souboru toho typu ve
Fedoře. Důsledkem je, že `thumb` i `thumb_large` u `image/bmp` vyjdou shodné (obojí
100×100); je to správný výstup, ne chyba manifestu - **nezvětšovat**.
