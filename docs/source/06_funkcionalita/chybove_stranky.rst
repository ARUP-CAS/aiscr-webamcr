Chybové stránky
===============

Zobrazování chybových stránek se řídí logikou Djanga popsané na webových stránkách `https://docs.djangoproject.com/en/5.0/ref/views/#error-views`.
Django má zabudované 4 základní chybové pohledy pro ošetření HTTP chyb.

404 (stránka nenalezena) pohled
--------------------------------
Pohled se volá v případě že Django nenajde stránku mezi žádnými definovanými URL. V takovém případě zobrazí šablonu `404.html`.

500 (chyba serveru) pohled
---------------------------
Pohled se volá v případě runtime chyby v kódu, která vede k neošetřené výjimce. V takovém případě zobrazí šablonu `500.html`.

403 (HTTP přístup zakázán) pohled
----------------------------------
Pohled se volá v případě zakázaného přístupu uživateli pomoci výjimky `PermissionDenied`. V takovém případě zobrazí šablonu `403.html`.

400 (špatný požadavek) pohled
----------------------------------
Pohled se volá v případě špatného požadavku ze strany klienta. V takovém případě zobrazí šablonu `400.html`.

Šablony
-------
Všechny šablony pro pohledy jsou umístěné v adresáři `webclient/templates`. Všechny mají styl AMČR s logem a obsahují možnost prekladu pomocí rossety.