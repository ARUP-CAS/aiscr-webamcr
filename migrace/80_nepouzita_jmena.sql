-- Zkontrolovat a odstranit nepoužitá jména z hesláře.
with pom AS
(
    SELECT os.id FROM osoba os
    LEFT JOIN adb adb1 ON adb1.autor_popisu = os.id
    LEFT JOIN adb adb2 ON adb2.autor_revize = os.id
    LEFT JOIN akce ak ON ak.hlavni_vedouci = os.id
    LEFT JOIN akce_vedouci av ON av.vedouci = os.id
    LEFT JOIN auth_user au ON au.osoba = os.id
    LEFT JOIN dokument_autor da ON da.autor = os.id
    LEFT JOIN dokument_osoba dos ON dos.osoba = os.id
    LEFT JOIN externi_zdroj_autor ea ON ea.autor = os.id
    LEFT JOIN externi_zdroj_editor ee ON ee.editor = os.id
    LEFT JOIN let l ON l.pozorovatel = os.id
    LEFT JOIN neident_akce_vedouci nv ON nv.vedouci = os.id
    LEFT JOIN projekt pr ON pr.vedouci_projektu = os.id
    LEFT JOIN samostatny_nalez sn ON sn.nalezce = os.id
    WHERE
    adb1.dokumentacni_jednotka is null AND
    adb2.dokumentacni_jednotka is null AND
    ak.archeologicky_zaznam is null AND
    av.id is null AND
    au.id is null AND
    da.id is null AND
    dos.id is null AND
    ea.id is null AND
    ee.id is null AND
    l.id is null AND
    nv.id is null AND
    pr.id is null AND
    sn.id is null
)
DELETE FROM osoba USING pom WHERE osoba.id = pom.id;

-- Vymazání odstraněných hesel z hesláře (opomenuto dříve)
DELETE FROM heslar WHERE ident_cely IN ('HES-000611', 'HES-000616', 'HES-000622');
