CORE coordTransform
===================

Modul coordTransform.

Funkce
------

.. py:function:: readCoef(table)

   Načtení tabulky s opravamy

.. py:function:: convertToJTSK(longitude, latitude, height)

   Provádí operaci convertToJTSK.

   :param longitude: Vstupní hodnota ``longitude`` pro danou operaci.
   :param latitude: Vstupní hodnota ``latitude`` pro danou operaci.
   :param height: Vstupní hodnota ``height`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: convertToWGS84(minusY, minusX, height)

   Provádí operaci convertToWGS84.

   :param minusY: Vstupní hodnota ``minusY`` pro danou operaci.
   :param minusX: Vstupní hodnota ``minusX`` pro danou operaci.
   :param height: Vstupní hodnota ``height`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: wgs84_to_bessel(latitude, longitude, altitude)

   Provádí operaci wgs84 to bessel.

   :param latitude: Vstupní hodnota ``latitude`` pro danou operaci.
   :param longitude: Vstupní hodnota ``longitude`` pro danou operaci.
   :param altitude: Vstupní hodnota ``altitude`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: bessel_to_wgs84(latitude, longitude, altitude)

   Provádí operaci bessel to wgs84.

   :param latitude: Vstupní hodnota ``latitude`` pro danou operaci.
   :param longitude: Vstupní hodnota ``longitude`` pro danou operaci.
   :param altitude: Vstupní hodnota ``altitude`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: bessel_to_jtsk(B, L)

   Provádí operaci bessel to jtsk.

   :param B: Vstupní hodnota ``B`` pro danou operaci.
   :param L: Vstupní hodnota ``L`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: jtsk_to_bessel(X05, Y05)

   Provádí operaci jtsk to bessel.

   :param X05: Vstupní hodnota ``X05`` pro danou operaci.
   :param Y05: Vstupní hodnota ``Y05`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: blht_to_geo_coords_wgs(b, l, h)

   Provádí operaci blht to geo coords wgs.

   :param b: Vstupní hodnota ``b`` pro danou operaci.
   :param l: Vstupní hodnota ``l`` pro danou operaci.
   :param h: Vstupní hodnota ``h`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: blht_to_geo_coords_bessel(b, l, h)

   Provádí operaci blht to geo coords bessel.

   :param b: Vstupní hodnota ``b`` pro danou operaci.
   :param l: Vstupní hodnota ``l`` pro danou operaci.
   :param h: Vstupní hodnota ``h`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: geo_coords_to_blh_bessel(X, Y, Z)

   Provádí operaci geo coords to blh bessel.

   :param X: Vstupní hodnota ``X`` pro danou operaci.
   :param Y: Vstupní hodnota ``Y`` pro danou operaci.
   :param Z: Vstupní hodnota ``Z`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: geo_coords_to_blh_wgs(X, Y, Z)

   Provádí operaci geo coords to blh wgs.

   :param X: Vstupní hodnota ``X`` pro danou operaci.
   :param Y: Vstupní hodnota ``Y`` pro danou operaci.
   :param Z: Vstupní hodnota ``Z`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: ETRF2JTSK05transform_coords(xs, ys, zs)

   Provádí operaci ETRF2JTSK05transform coords.

   :param xs: Vstupní hodnota ``xs`` pro danou operaci.
   :param ys: Vstupní hodnota ``ys`` pro danou operaci.
   :param zs: Vstupní hodnota ``zs`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: JTSK052ETRFtransform_coords(xs, ys, zs)

   Provádí operaci JTSK052ETRFtransform coords.

   :param xs: Vstupní hodnota ``xs`` pro danou operaci.
   :param ys: Vstupní hodnota ``ys`` pro danou operaci.
   :param zs: Vstupní hodnota ``zs`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: WGS2ETRFtransform_coords(xs, ys, zs)

   Provádí operaci WGS2ETRFtransform coords.

   :param xs: Vstupní hodnota ``xs`` pro danou operaci.
   :param ys: Vstupní hodnota ``ys`` pro danou operaci.
   :param zs: Vstupní hodnota ``zs`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: ETRF2WGStransform_coords(xs, ys, zs)

   Provádí operaci ETRF2WGStransform coords.

   :param xs: Vstupní hodnota ``xs`` pro danou operaci.
   :param ys: Vstupní hodnota ``ys`` pro danou operaci.
   :param zs: Vstupní hodnota ``zs`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: jtsk05_to_jtsk(x05, y05)

   Provádí operaci jtsk05 to jtsk.

   :param x05: Vstupní hodnota ``x05`` pro danou operaci.
   :param y05: Vstupní hodnota ``y05`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: jtsk_to_jtsk05(X, Y)

   Provádí operaci jtsk to jtsk05.

   :param X: Vstupní hodnota ``X`` pro danou operaci.
   :param Y: Vstupní hodnota ``Y`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: get_multi_transform_to_sjtsk(wgs_points)

   Vrací multi transform to sjtsk.

   :param wgs_points: Vstupní hodnota ``wgs_points`` pro danou operaci.
   :return: Vrací načtená data odpovídající vstupním parametrům.

.. py:function:: get_multi_transform_to_wgs84(jtsk_points)

   Vrací multi transform to wgs84.

   :param jtsk_points: Vstupní hodnota ``jtsk_points`` pro danou operaci.
   :return: Vrací načtená data odpovídající vstupním parametrům.

.. py:function:: contains_two_floats(text)

   Provádí operaci contains two floats.

   :param text: Vstupní hodnota ``text`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: transform_geom(geom, transFunc)

   Transformuje geom.

   :param geom: Vstupní hodnota ``geom`` pro danou operaci.
   :param transFunc: Vstupní hodnota ``transFunc`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: transform_geom_to_sjtsk(geom)

   Transformuje geom to sjtsk.

   :param geom: Vstupní hodnota ``geom`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: transform_geom_to_wgs84(geom)

   Transformuje geom to wgs84.

   :param geom: Vstupní hodnota ``geom`` pro danou operaci.
   :return: Vrací výsledek provedené operace.
