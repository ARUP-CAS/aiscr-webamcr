CORE filtry
===========

Definice filtrů.

Třídy
------

.. py:class:: GeomIntersectsFilterMixin

   Mixin pro prostorové filtrování výpisu podle obdélníku (případně polygonu) nakresleného
   na mapě v záložce filtru. Hodnota se předává jako WKT v souřadnicovém systému WGS84
   (EPSG:4326) ve skrytém poli ``geom_filter``.

   Aplikuje se lookup ``__intersects`` (tj. **jakýkoli překryv** s vybranou plochou, nikoli plné
   obsažení jako u ``__within``) – díky tomu se do výběru dostanou i záznamy zasahující přes okraj.

   Při nevalidní WKT hodnotě filtr **nevrací žádné záznamy** (fail-closed), aby uživatel nedostal
   nefiltrovaný výpis v domnění, že je mapový výběr aplikován.

   Každý potomek nastaví :attr:`geom_filter_lookup` na cestu k geometrickému poli modelu
   (např. ``"geom"`` pro přímou bodovou geometrii nebo
   ``"archeologicky_zaznam__dokumentacni_jednotky_akce__pian__geom"`` pro geometrii přes Pian).

   Volitelně lze nastavit :attr:`geom_filter_presnost_lookup` na cestu k poli přesnosti PIANu.
   Pak se PIAN s přesností „poloha podle katastru“ vybírá podle svého reprezentativního bodu
   (``ST_PointOnSurface``), nikoli podle celého katastrálního polygonu – shodně s tím, jak je
   takový PIAN zobrazen v mapě (WYSIWYG: co je vidět jako bod, podle bodu se i vybírá).

   **Metody:**

   .. py:method:: filter_geom()

      Filtruje queryset podle geometrie nakreslené na mapě.

      :param queryset: Queryset k prostorovému filtrování.
      :param name: Název filtru (``geom_filter``), nevyužívá se.
      :param value: WKT geometrie v EPSG:4326 ze skrytého pole; prázdná hodnota filtr přeskočí.

      :return: Vrací queryset omezený na záznamy protínající zadanou geometrii, nebo prázdný
              queryset, pokud je hodnota nevalidní.

