UPDATE vyskovy_bod SET ident_cely = adb.ident_cely || RIGHT(vyskovy_bod.ident_cely,6)
FROM adb WHERE adb.dokumentacni_jednotka = vyskovy_bod.adb;
