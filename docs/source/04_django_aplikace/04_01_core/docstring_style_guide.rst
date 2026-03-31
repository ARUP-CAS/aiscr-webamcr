Docstring style guide
======================

Tento dokument sjednocuje pravidla pro psaní docstringů v projektu AMČR.
Cílem je, aby docstringy byly konzistentní, srozumitelné a užitečné pro vývojáře
i generování dokumentace.

Základní principy
-----------------

* **Popisuj účel, ne název funkce.** Docstring má vysvětlit, proč funkce/třída existuje
  a jakou roli má v aplikaci.
* **Buď konkrétní.** Vyhýbej se obecným formulacím typu „zajišťuje logiku funkce“.
* **Udržuj stručnost.** Preferuj krátký a výstižný popis (1–3 věty).
* **Dodržuj jednotný formát.** V projektu používej reStructuredText pole
  ``:param:``, ``:return:`` a podle potřeby ``:raises:``.
* **Popiš doménový kontext.** Uveď, jak vstupy a výstupy souvisí s AMČR doménou
  (např. identifikátory, stavové přechody, export, přístupnost dat).

Co má obsahovat docstring funkce/metody
---------------------------------------

1. Jednořádkové shrnutí účelu.
2. Popis parametrů (jen těch, které jsou relevantní):

   * ``:param <nazev>:`` význam parametru v kontextu aplikace,
   * případně omezení (formát, validní rozsah, očekávaný stav).

3. Popis návratové hodnoty:

   * ``:return:`` co funkce vrací a jak má být výsledek interpretován.

4. Volitelně výjimky:

   * ``:raises <Vyjimka>:`` kdy a proč může být vyhozena.

Doporučený vzor pro funkci
--------------------------

.. code-block:: python

   def get_export_payload(record_id: str) -> dict:
       """Sestaví datový payload pro export archeologického záznamu.

       :param record_id: Identifikátor záznamu ve formátu ``C-XX-YYYYNNNNN``.
       :return: Slovník s normalizovanými daty použitelný pro XML/JSON export.
       :raises ValueError: Pokud identifikátor neodpovídá očekávanému formátu.
       """

Co má obsahovat docstring třídy
-------------------------------

* Stručně popiš odpovědnost třídy v architektuře (např. View, Form, Service,
  Repository connector).
* U tříd se složitým chováním doplň klíčové informace o lifecycle nebo vazbě
  na externí systém.

Doporučený vzor pro třídu
-------------------------

.. code-block:: python

   class ExportView(LoginRequiredMixin, View):
       """Obsluhuje požadavky na export dat archeologického záznamu."""

Doporučení pro kvalitu
----------------------

* Neopakuj informace, které jsou zřejmé ze signatury.
* Neuváděj neaktuální informace — při změně chování aktualizuj i docstring.
* U veřejných API (views, services, utility funkce) preferuj detailnější popis
  než u privátních helperů.
* U interních helperů stačí krátký popis, pokud je chování přímočaré.

Anti-patterny
-------------

Nedoporučené formulace:

* „Zajišťuje logiku funkce …“
* „Zapouzdřuje chování třídy …“
* Obecné věty bez kontextu parametrů a návratové hodnoty.

Checklist před commitem
-----------------------

* Docstring odpovídá aktuálnímu chování kódu.
* Parametry mají popsaný význam, ne jen název.
* Návratová hodnota je interpretovatelná bez čtení implementace.
* Formát je konzistentní s tímto style guide.
