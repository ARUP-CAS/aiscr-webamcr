CORE coordTransform
===================

Modul coordTransform.

Funkce
------

.. py:function:: readCoef(table)

   Načtení tabulky s opravamy

   :param table: Parametr ``table`` slouží jako vstup pro logiku funkce ``readCoef``.

.. py:function:: convertToJTSK(longitude, latitude, height)

   Provádí operaci convertToJTSK.

   :param longitude: Číselná hodnota ``longitude`` použitá při výpočtu nebo transformaci.
   :param latitude: Číselná hodnota ``latitude`` použitá při výpočtu nebo transformaci.
   :param height: Číselná hodnota ``height`` použitá při výpočtu nebo transformaci.

   :return: Vrací seznam.
   :raises Exception: Vyvolá se při splnění podmínky ``latitude < 40 or latitude > 60 or longitude < 5 or (longitude > 25)``.

.. py:function:: convertToWGS84(minusY, minusX, height)

   Provádí operaci convertToWGS84.

   :param minusY: Číselná hodnota ``minusY`` použitá při výpočtu nebo transformaci.
   :param minusX: Číselná hodnota ``minusX`` použitá při výpočtu nebo transformaci.
   :param height: Číselná hodnota ``height`` použitá při výpočtu nebo transformaci.

   :return: Vrací seznam.
   :raises Exception: Vyvolá se při splnění podmínky ``minusY < -905000 or minusY > -400000 or minusX < -1230000 or (minusX > -930000)``.

.. py:function:: wgs84_to_bessel(latitude, longitude, altitude)

   Provádí operaci wgs84 to bessel.

   :param latitude: Číselná hodnota ``latitude`` použitá při výpočtu nebo transformaci.
   :param longitude: Číselná hodnota ``longitude`` použitá při výpočtu nebo transformaci.
   :param altitude: Parametr ``altitude`` slouží jako vstup pro logiku funkce ``wgs84_to_bessel``.

   :return: Vrací seznam.

.. py:function:: bessel_to_wgs84(latitude, longitude, altitude)

   Provádí operaci bessel to wgs84.

   :param latitude: Číselná hodnota ``latitude`` použitá při výpočtu nebo transformaci.
   :param longitude: Číselná hodnota ``longitude`` použitá při výpočtu nebo transformaci.
   :param altitude: Parametr ``altitude`` slouží jako vstup pro logiku funkce ``bessel_to_wgs84``.

   :return: Vrací seznam.

.. py:function:: bessel_to_jtsk(B, L)

   Provádí operaci bessel to jtsk.

   :param B: Geodetická hodnota vstupního parametru používaná ve výpočtu transformace.
   :param L: Parametr ``L`` se předává do volání ``radians()``.

   :return: Vrací seznam.

.. py:function:: jtsk_to_bessel(X05, Y05)

   Provádí operaci jtsk to bessel.

   :param X05: Číselná hodnota ``X05`` použitá při výpočtu nebo transformaci.
   :param Y05: Číselná hodnota ``Y05`` použitá při výpočtu nebo transformaci.

   :return: Vrací seznam.

.. py:function:: blht_to_geo_coords_wgs(b, l, h)

   Provádí operaci blht to geo coords wgs.

   :param b: Geodetická hodnota vstupního parametru používaná ve výpočtu transformace.
   :param l: Parametr ``l`` se předává do volání ``cos()``, ``sin()``.
   :param h: Parametr ``h`` slouží jako vstup pro logiku funkce ``blht_to_geo_coords_wgs``.

   :return: Vrací seznam.

.. py:function:: blht_to_geo_coords_bessel(b, l, h)

   Provádí operaci blht to geo coords bessel.

   :param b: Geodetická hodnota vstupního parametru používaná ve výpočtu transformace.
   :param l: Parametr ``l`` se předává do volání ``cos()``, ``sin()``.
   :param h: Parametr ``h`` slouží jako vstup pro logiku funkce ``blht_to_geo_coords_bessel``.

   :return: Vrací seznam.

.. py:function:: geo_coords_to_blh_bessel(X, Y, Z)

   Provádí operaci geo coords to blh bessel.

   :param X: Číselná hodnota ``X`` použitá při výpočtu nebo transformaci.
   :param Y: Číselná hodnota ``Y`` použitá při výpočtu nebo transformaci.
   :param Z: Parametr ``Z`` se předává do volání ``atan()``.

   :return: Vrací seznam.

.. py:function:: geo_coords_to_blh_wgs(X, Y, Z)

   Provádí operaci geo coords to blh wgs.

   :param X: Číselná hodnota ``X`` použitá při výpočtu nebo transformaci.
   :param Y: Číselná hodnota ``Y`` použitá při výpočtu nebo transformaci.
   :param Z: Parametr ``Z`` se předává do volání ``atan()``.

   :return: Vrací seznam.

.. py:function:: ETRF2JTSK05transform_coords(xs, ys, zs)

   Provádí operaci ETRF2JTSK05transform coords.

   :param xs: Číselná hodnota ``xs`` použitá při výpočtu nebo transformaci.
   :param ys: Číselná hodnota ``ys`` použitá při výpočtu nebo transformaci.
   :param zs: Parametr ``zs`` slouží jako vstup pro logiku funkce ``ETRF2JTSK05transform_coords``.

   :return: Vrací seznam.

.. py:function:: JTSK052ETRFtransform_coords(xs, ys, zs)

   Provádí operaci JTSK052ETRFtransform coords.

   :param xs: Číselná hodnota ``xs`` použitá při výpočtu nebo transformaci.
   :param ys: Číselná hodnota ``ys`` použitá při výpočtu nebo transformaci.
   :param zs: Parametr ``zs`` slouží jako vstup pro logiku funkce ``JTSK052ETRFtransform_coords``.

   :return: Vrací seznam.

.. py:function:: WGS2ETRFtransform_coords(xs, ys, zs)

   Provádí operaci WGS2ETRFtransform coords.

   :param xs: Číselná hodnota ``xs`` použitá při výpočtu nebo transformaci.
   :param ys: Číselná hodnota ``ys`` použitá při výpočtu nebo transformaci.
   :param zs: Parametr ``zs`` slouží jako vstup pro logiku funkce ``WGS2ETRFtransform_coords``.

   :return: Vrací seznam.

.. py:function:: ETRF2WGStransform_coords(xs, ys, zs)

   Provádí operaci ETRF2WGStransform coords.

   :param xs: Číselná hodnota ``xs`` použitá při výpočtu nebo transformaci.
   :param ys: Číselná hodnota ``ys`` použitá při výpočtu nebo transformaci.
   :param zs: Parametr ``zs`` slouží jako vstup pro logiku funkce ``ETRF2WGStransform_coords``.

   :return: Vrací seznam.

.. py:function:: jtsk05_to_jtsk(x05, y05)

   Provádí operaci jtsk05 to jtsk.

   :param x05: Číselná hodnota ``x05`` použitá při výpočtu nebo transformaci.
   :param y05: Číselná hodnota ``y05`` použitá při výpočtu nebo transformaci.

   :return: Vrací seznam.

.. py:function:: jtsk_to_jtsk05(X, Y)

   Provádí operaci jtsk to jtsk05.

   :param X: Číselná hodnota ``X`` použitá při výpočtu nebo transformaci.
   :param Y: Číselná hodnota ``Y`` použitá při výpočtu nebo transformaci.

   :return: Vrací seznam.

.. py:function:: get_multi_transform_to_sjtsk(wgs_points)

   Vrací multi transform to sjtsk.

   :param wgs_points: Parametr ``wgs_points`` slouží jako vstup pro logiku funkce ``get_multi_transform_to_sjtsk``.

   :return: Vrací proměnná ``my``.

.. py:function:: get_multi_transform_to_wgs84(jtsk_points)

   Vrací multi transform to wgs84.

   :param jtsk_points: Parametr ``jtsk_points`` slouží jako vstup pro logiku funkce ``get_multi_transform_to_wgs84``.

   :return: Vrací proměnná ``my``.

.. py:function:: contains_two_floats(text)

   Provádí operaci contains two floats.

   :param text: Číselná hodnota ``text`` použitá při výpočtu nebo transformaci.

   :return: Vrací výsledek volání ``bool()``.

.. py:function:: transform_geom(geom, transFunc)

   Transformuje geom. v aplikaci.

   :param geom: Parametr ``geom`` předává se do volání ``isinstance()``, pracuje se s atributy ``find``, ``replace``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param transFunc: Parametr ``transFunc`` slouží jako vstup pro logiku funkce ``transform_geom``.

   :return: Vrací n-tici.

.. py:function:: transform_geom_to_sjtsk(geom)

   Transformuje geom to sjtsk.

   :param geom: Parametr ``geom`` předává se do volání ``transform_geom()``, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``transform_geom()``.

.. py:function:: transform_geom_to_wgs84(geom)

   Transformuje geom to wgs84.

   :param geom: Parametr ``geom`` předává se do volání ``transform_geom()``, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``transform_geom()``.
