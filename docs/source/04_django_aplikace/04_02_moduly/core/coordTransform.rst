CORE coordTransform
===================

Modul coordTransform.

Funkce
------

.. py:function:: readCoef(table)

   Načtení tabulky s opravamy

   :param table: Název nebo typ ``table`` používaný pro volbu cílové logiky.

.. py:function:: convertToJTSK(longitude, latitude, height)

   Provádí operaci convertToJTSK.

   :param longitude: Číselná hodnota ``longitude`` použitá při výpočtu nebo transformaci.
   :param latitude: Číselná hodnota ``latitude`` použitá při výpočtu nebo transformaci.
   :param height: Číselná hodnota ``height`` použitá při výpočtu nebo transformaci.

.. py:function:: convertToWGS84(minusY, minusX, height)

   Provádí operaci convertToWGS84.

   :param minusY: Číselná hodnota ``minusY`` použitá při výpočtu nebo transformaci.
   :param minusX: Číselná hodnota ``minusX`` použitá při výpočtu nebo transformaci.
   :param height: Číselná hodnota ``height`` použitá při výpočtu nebo transformaci.

.. py:function:: wgs84_to_bessel(latitude, longitude, altitude)

   Provádí operaci wgs84 to bessel.

   :param latitude: Číselná hodnota ``latitude`` použitá při výpočtu nebo transformaci.
   :param longitude: Číselná hodnota ``longitude`` použitá při výpočtu nebo transformaci.
   :param altitude: Číselná nebo geometrická hodnota `altitude` použitá při výpočtu nebo transformaci.

.. py:function:: bessel_to_wgs84(latitude, longitude, altitude)

   Provádí operaci bessel to wgs84.

   :param latitude: Číselná hodnota ``latitude`` použitá při výpočtu nebo transformaci.
   :param longitude: Číselná hodnota ``longitude`` použitá při výpočtu nebo transformaci.
   :param altitude: Číselná nebo geometrická hodnota `altitude` použitá při výpočtu nebo transformaci.

.. py:function:: bessel_to_jtsk(B, L)

   Provádí operaci bessel to jtsk.

   :param B: Geodetická hodnota vstupního parametru používaná ve výpočtu transformace.
   :param L: Číselná nebo geometrická hodnota `L` použitá při výpočtu nebo transformaci.

.. py:function:: jtsk_to_bessel(X05, Y05)

   Provádí operaci jtsk to bessel.

   :param X05: Číselná hodnota ``X05`` použitá při výpočtu nebo transformaci.
   :param Y05: Číselná hodnota ``Y05`` použitá při výpočtu nebo transformaci.

.. py:function:: blht_to_geo_coords_wgs(b, l, h)

   Provádí operaci blht to geo coords wgs.

   :param b: Geodetická hodnota vstupního parametru používaná ve výpočtu transformace.
   :param l: Číselná nebo geometrická hodnota `l` použitá při výpočtu nebo transformaci.
   :param h: Číselná nebo geometrická hodnota `h` použitá při výpočtu nebo transformaci.

.. py:function:: blht_to_geo_coords_bessel(b, l, h)

   Provádí operaci blht to geo coords bessel.

   :param b: Geodetická hodnota vstupního parametru používaná ve výpočtu transformace.
   :param l: Číselná nebo geometrická hodnota `l` použitá při výpočtu nebo transformaci.
   :param h: Číselná nebo geometrická hodnota `h` použitá při výpočtu nebo transformaci.

.. py:function:: geo_coords_to_blh_bessel(X, Y, Z)

   Provádí operaci geo coords to blh bessel.

   :param X: Číselná hodnota ``X`` použitá při výpočtu nebo transformaci.
   :param Y: Číselná hodnota ``Y`` použitá při výpočtu nebo transformaci.
   :param Z: Číselná nebo geometrická hodnota `Z` použitá při výpočtu nebo transformaci.

.. py:function:: geo_coords_to_blh_wgs(X, Y, Z)

   Provádí operaci geo coords to blh wgs.

   :param X: Číselná hodnota ``X`` použitá při výpočtu nebo transformaci.
   :param Y: Číselná hodnota ``Y`` použitá při výpočtu nebo transformaci.
   :param Z: Číselná nebo geometrická hodnota `Z` použitá při výpočtu nebo transformaci.

.. py:function:: ETRF2JTSK05transform_coords(xs, ys, zs)

   Provádí operaci ETRF2JTSK05transform coords.

   :param xs: Číselná hodnota ``xs`` použitá při výpočtu nebo transformaci.
   :param ys: Číselná hodnota ``ys`` použitá při výpočtu nebo transformaci.
   :param zs: Číselná nebo geometrická hodnota `zs` použitá při výpočtu nebo transformaci.

.. py:function:: JTSK052ETRFtransform_coords(xs, ys, zs)

   Provádí operaci JTSK052ETRFtransform coords.

   :param xs: Číselná hodnota ``xs`` použitá při výpočtu nebo transformaci.
   :param ys: Číselná hodnota ``ys`` použitá při výpočtu nebo transformaci.
   :param zs: Číselná nebo geometrická hodnota `zs` použitá při výpočtu nebo transformaci.

.. py:function:: WGS2ETRFtransform_coords(xs, ys, zs)

   Provádí operaci WGS2ETRFtransform coords.

   :param xs: Číselná hodnota ``xs`` použitá při výpočtu nebo transformaci.
   :param ys: Číselná hodnota ``ys`` použitá při výpočtu nebo transformaci.
   :param zs: Číselná nebo geometrická hodnota `zs` použitá při výpočtu nebo transformaci.

.. py:function:: ETRF2WGStransform_coords(xs, ys, zs)

   Provádí operaci ETRF2WGStransform coords.

   :param xs: Číselná hodnota ``xs`` použitá při výpočtu nebo transformaci.
   :param ys: Číselná hodnota ``ys`` použitá při výpočtu nebo transformaci.
   :param zs: Číselná nebo geometrická hodnota `zs` použitá při výpočtu nebo transformaci.

.. py:function:: jtsk05_to_jtsk(x05, y05)

   Provádí operaci jtsk05 to jtsk.

   :param x05: Číselná hodnota ``x05`` použitá při výpočtu nebo transformaci.
   :param y05: Číselná hodnota ``y05`` použitá při výpočtu nebo transformaci.

.. py:function:: jtsk_to_jtsk05(X, Y)

   Provádí operaci jtsk to jtsk05.

   :param X: Číselná hodnota ``X`` použitá při výpočtu nebo transformaci.
   :param Y: Číselná hodnota ``Y`` použitá při výpočtu nebo transformaci.

.. py:function:: get_multi_transform_to_sjtsk(wgs_points)

   Vrací multi transform to sjtsk.

   :param wgs_points: Doménový objekt `wgs_points`, se kterým funkce pracuje.

.. py:function:: get_multi_transform_to_wgs84(jtsk_points)

   Vrací multi transform to wgs84.

   :param jtsk_points: Doménový objekt `jtsk_points`, se kterým funkce pracuje.

.. py:function:: contains_two_floats(text)

   Provádí operaci contains two floats.

   :param text: Číselná hodnota ``text`` použitá při výpočtu nebo transformaci.

.. py:function:: transform_geom(geom, transFunc)

   Transformuje geom. v aplikaci.

   :param geom: Doménový objekt `geom`, se kterým funkce pracuje.
   :param transFunc: Číselná nebo geometrická hodnota `transFunc` použitá při výpočtu nebo transformaci.

.. py:function:: transform_geom_to_sjtsk(geom)

   Transformuje geom to sjtsk.

   :param geom: Doménový objekt `geom`, se kterým funkce pracuje.

.. py:function:: transform_geom_to_wgs84(geom)

   Transformuje geom to wgs84.

   :param geom: Doménový objekt `geom`, se kterým funkce pracuje.
