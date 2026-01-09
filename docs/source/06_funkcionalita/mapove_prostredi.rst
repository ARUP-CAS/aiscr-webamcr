Dokumentace mapového prostředí AMČR
====================================

.. TODO: dokončit zpracování dokumentace mapového prostředí AMČR

Požadavky na geometrie v ukládané do AMČR
=========================================

1. Kontrolovat Self-intersection pro linii a polygon
2. Kontrolovat příliš krátké segmenty
3. Zajistit uložení polygonu pouze se třemi a více vertexy
4. Zakázat: Null geometry
5. Multipart feature nesmí být nikdy ze vstupu


Implementace
============

.. TODO


Sada testů a příkladů pro validaci geometrie
============================================

Validace přesnosti zadaných bodů
-------------------------------

- Pro geometrii S-JTSK je minimální vzdálenost mezi dvěma po sobě jdoucími body
  **0.11 m**.
- Pro geometrii WGS-84 je minimální vzdálenost mezi dvěma po sobě jdoucími body
  **0.000001°**.


Validace geometrie
------------------

.. TODO

Validace bodu
~~~~~~~~~~~~~

.. TODO

Validace linie
~~~~~~~~~~~~~

.. TODO

Validace polygonu
~~~~~~~~~~~~~~~~~

.. TODO

Validace multi-geometrií a kolekcí
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. TODO

Rychlá kontrola validity v databázi
==================================

Validace PIAN
-------------

::

   -- WGS-84
   SELECT id, validateGeom(st_astext(geom)), st_astext(geom)
   FROM public.pian
   WHERE geom IS NOT NULL
     AND validateGeom(st_astext(geom)) <> 'valid';

   -- S-JTSK
   SELECT id, validateGeom(st_astext(geom_sjtsk)), st_astext(geom_sjtsk)
   FROM public.pian
   WHERE geom_sjtsk IS NOT NULL
     AND validateGeom(st_astext(geom_sjtsk)) <> 'valid';

   -- statistika
   SELECT validateGeom(st_astext(geom)), COUNT(*)
   FROM public.pian
   WHERE geom IS NOT NULL
     AND validateGeom(st_astext(geom)) <> 'valid'
   GROUP BY validateGeom(st_astext(geom));
