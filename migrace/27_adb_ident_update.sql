UPDATE adb INNER JOIN vyskovy_bod ON adb.dokumentacni_jednotka = vyskovy_bod.adb SET vyskovy_bod.ident_cely = adb.ident_cely || RIGHT(vyskovy_bod.ident_cely,6);
