# Placeholder soubory (statická sada)

Hotové, **plně funkční** minimální soubory pro každý podporovaný mimetype + katalog
`placeholder_manifest.json` (mimetype → soubor, **napevno uložený `sha512` a `size`**).

Tuto sadu používá `ocfl_shrink.py --placeholders <tento adresář>` (náhrada orig v OCFL)
i Django příkaz `shrink_soubor_hashes --placeholder-manifest .../placeholder_manifest.json`
(update `soubor.sha_512`). Manifest je **jediný zdroj hashů** → hash zapsaný do OCFL je
totožný s hashem v DB. `ocfl_shrink.py` při startu ověří, že `sha512` i velikost každého
souboru odpovídají manifestu (ochrana proti rozejití souborů a manifestu).

Sada je statická a verzovaná v gitu; **negeneruje se za běhu**. Mimetypy odpovídají
`Soubor.get_file_extension_by_mime()` (+ alias `text/rtf`).

Provenience (jak byly soubory jednorázově vyrobeny):

- png, jpeg, gif, bmp, tiff, svg, txt, csv, pdf, rtf, zip, OOXML docx/xlsx, ODF odt/ods
  — sestaveny programově (Python stdlib + 1×1 rastry).
- `*.heic`/`*.heif` — pillow-heif; `*.rar` — WinRAR; `*.7z` — py7zr; `*.xls` — xlwt;
  `*.doc` — MS Word (uloženo jako Word 97-2003).

Pokud bys potřeboval sadu změnit (nový mimetype, jiný obsah), nahraď příslušný soubor
a **přepočítej `placeholder_manifest.json`** (sha512 + size), jinak `ocfl_shrink.py`
skončí chybou kontroly.
