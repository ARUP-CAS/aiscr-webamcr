CORE filtry
===========

Definice filtrů.

Třídy
------

.. py:class:: GeomWithinFilterMixin

   Mixin pro prostorové filtrování výpisu podle obdélníku (případně polygonu) nakresleného
   na mapě v záložce filtru. Hodnota se předává jako WKT v souřadnicovém systému WGS84
   (EPSG:4326) ve skrytém poli ``geom_filter`` a aplikuje se lookup ``__intersects``.

   Každý potomek nastaví :attr:`geom_filter_lookup` na cestu k geometrickému poli modelu
   (např. ``"geom"`` pro přímou bodovou geometrii nebo
   ``"archeologicky_zaznam__dokumentacni_jednotky_akce__pian__geom"`` pro geometrii přes Pian).

   **Metody:**

   .. py:method:: filter_geom()

      Filtruje queryset podle geometrie nakreslené na mapě.

      :param queryset: Queryset k prostorovému filtrování.
      :param name: Název filtru (``geom_filter``), nevyužívá se.
      :param value: WKT geometrie v EPSG:4326 ze skrytého pole; prázdná hodnota filtr přeskočí.

      :return: Vrací queryset omezený na záznamy protínající zadanou geometrii.

