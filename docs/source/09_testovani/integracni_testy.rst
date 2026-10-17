.. _integracni-testy:

Integrační testy
=========================

Integrační testy ověřují spolupráci více vrstev aplikace přes skutečné HTTP požadavky.
Test uploadu fotografie prochází cestou nginx → uWSGI → Django a nevyužívá Django test client.
Před spuštěním je nutné na cílové prostředí nasadit ověřovanou verzi aplikace **i proxy**.

Spuštění testů
--------------

Test ``api/tests/test_upload_foto_integration.py`` pracuje s již běžící aplikací, existujícím
vyhrazeným testovacím nálezem a tokenem s oprávněním ``soubor_nahrat_pas`` pro tento nález.
Nezakládá nález ani testovací databázi. Nastavení API musí umožňovat opakovaná volání bez
throttlingu. Pro test používejte vyhrazený nález a token, který nevkládejte do Git.

Povolená prostředí
~~~~~~~~~~~~~~~~~~

Pro spuštění musí platit jedna z podmínek:

* Cíl je přesně **https://amcr-test.aiscr.cz** na standardním HTTPS portu. Na této testovací
  aplikaci lze test spustit i při ``DEBUG=False`` v testovacím procesu i cílové aplikaci.
* Cíl je loopback adresa ``localhost``, ``127.0.0.1`` nebo ``[::1]`` a testovací proces má
  ``DEBUG=True``. URL musí vést na lokální nginx, například ``http://127.0.0.1:8080``, nikoliv
  přímo na Django/uWSGI. Nepoužívejte tunel na produkční aplikaci.

Produkční doména ``amcr.aiscr.cz`` a jiné vzdálené domény jsou odmítnuty **i s DEBUG=True**.
Pojistka se ověřuje před vytvořením velkého PNG a před síťovým provozem. Nenastavená cílová
adresa nebo lokální cíl s ``DEBUG=False`` test přeskočí. Nepovolená URL či chybějící token
nebo identifikátor nálezu při nastavené cílové adrese způsobí chybu konfigurace.

Proměnná ``PAS_UPLOAD_BASE_URL`` obsahuje pouze adresu serveru: ``https://amcr-test.aiscr.cz``.
Přihlašovací cesta ``/accounts/login/?next=/`` do ní nepatří. Test používá Bearer token,
nikoli přihlášení přes webový formulář. URL nesmí obsahovat uživatelské údaje, cestu kromě
volitelného koncového lomítka, query ani fragment. Přesměrování HTTP klient nenásleduje,
takže přesměrování z testovací domény na produkci neodešle token ani soubor na produkci.

Příkaz ke spuštění
~~~~~~~~~~~~~~~~~~

V prostředí nastavte následující proměnné:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Proměnná
     - Hodnota
   * - ``PAS_UPLOAD_BASE_URL``
     - ``https://amcr-test.aiscr.cz`` nebo povolená lokální adresa nginx
   * - ``PAS_UPLOAD_TOKEN``
     - Bearer token oprávněného testovacího uživatele
   * - ``PAS_UPLOAD_IDENT_CELY``
     - Identifikátor existujícího vyhrazeného testovacího nálezu

Z adresáře ``webclient/`` spusťte se settings modulem nastaveným pro testovací proces::

   python manage.py test api.tests.test_upload_foto_integration \
       --testrunner django.test.runner.DiscoverRunner

Pro lokální cíl přidejte ``--debug-mode``. Standardní Django test runner totiž jinak
přepne ``DEBUG`` na ``False``; test sám DEBUG nezapíná. Pro vzdálenou testovací aplikaci
není ``--debug-mode`` potřeba a DEBUG může zůstat vypnutý.

Vyhodnocení výsledků testu
--------------------------

Výsledek vypisuje Django test runner do terminálu. Každá kombinace velikosti, způsobu přenosu
a opakování je samostatný subtest. Úspěch vyžaduje úplnou odpověď HTTP ``422``, typ
``application/json`` a očekávaný popis překročené velikosti v poli ``detail``. Odpověď ``413``,
``502``, timeout, neúplná odpověď nebo přesměrování znamenají neúspěch. Jedno volání má limit
600 sekund. Test posílá ``Accept-Language: en`` a ověřuje anglický text chyby.

Požadavky odmítnuté aplikací mají neúspěšný ``ApiRequestLog``; požadavky odmítnuté přímo
nginx jsou pouze v logu proxy. Po běhu lze na vyhrazeném nálezu ověřit, že se nepřipojily
žádné fotografie. Integrační test sám nečte databázi cílové aplikace.

Struktura popisu scénáře
------------------------

Stejně jako u Selenium testů popis obsahuje ID, stručný popis, uživatelskou roli,
předpoklady, kroky, testovací data a očekávané výsledky. Scénáře jsou seskupeny podle aplikací.

PAS API
--------

PAS-HTTP-001 — Nadlimitní fotografie
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Soubor:** ``webclient/api/tests/test_upload_foto_integration.py``.

**Metoda:** ``UploadFotoHttpIntegrationTests.test_oversized_png_returns_422_through_proxy``.

**Popis:** Ověření shodné odpovědi při překročení limitu fotografie v aplikaci i limitu
celého HTTP těla v nginx. Podrobnosti limitů jsou v :doc:`/05_integrace/pas_api`.

**Uživatelská role:** Uživatel s oprávněním ``soubor_nahrat_pas`` pro zvolený nález.

**Předpoklady:** Povolené prostředí, nasazená aplikace a proxy, existující
testovací nález, platný token a možnost opakovaných požadavků bez throttlingu. Klient potřebuje
dostatek RAM pro PNG o velikosti až 512 MiB. Server a nginx mohou používat dočasné soubory.

**Kroky:**

#. V paměti vytvořit malé platné PNG a doplnit platný pomocný chunk na požadovanou velikost.
#. Po částech vypočítat SHA-512 nad PNG a sestavit ``Content-Digest``.
#. Odeslat soubor jako multipart požadavek na ``POST /api/pas/nalez/{ident_cely}/upload-foto``.
#. Ověřit kód, JSON typ odpovědi a konkrétní popis chyby.
#. Každý případ zopakovat třikrát. Pro 261 MiB navíc kombinovat Content-Length a chunked
   přenos s přítomností a nepřítomností hlavičky ``Expect: 100-continue``.

**Testovací data:** PNG o velikostech 250 MiB + 1 bajt, 255 MiB, 261 MiB a 512 MiB. Souborový
limit aplikace se nepřepisuje. PNG vznikají jeden po druhém pouze v paměti klienta, nejsou
součástí Git a klient je neukládá na disk. Digest i přenos se zpracovávají po částech bez další
úplné kopie multipart těla.

**Očekávané výsledky:** Každé volání vrátí HTTP ``422`` a JSON
``{"detail": "The uploaded file exceeds the maximum allowed size."}``. Soubor nad 250 MiB,
jehož celé multipart tělo nepřesahuje 260 MiB, odmítne aplikace; tělo nad 260 MiB odmítne nginx.
Žádný z případů nesmí skončit HTTP ``413``, HTTP ``502`` ani timeoutem.
