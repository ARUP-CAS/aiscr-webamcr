CORE coordTransform
===================

Modul coordTransform.

Funkce
------

.. py:function:: readCoef(table)

   Načtení tabulky s opravamy

   :param table: Slovník, do kterého se načtou korekční koeficienty ze souboru ``table_yx_3_v1710.dat``.

.. py:function:: convertToJTSK(longitude, latitude, height)

   Převede souřadnice z elipsoidu WGS-84 do souřadnicového systému S-JTSK.

   :param longitude: Zeměpisná délka ve stupních (WGS-84).
   :param latitude: Zeměpisná šířka ve stupních (WGS-84).
   :param height: Výška nad elipsoidem v metrech (výchozí 0).

       :return: Vrací seznam.
       :raises Exception: Vyvolá se při splnění podmínky ``latitude < 40 or latitude > 60 or longitude < 5 or (longitude > 25)``.

.. py:function:: convertToWGS84(minusY, minusX, height)

   Převede souřadnice ze souřadnicového systému S-JTSK do elipsoidu WGS-84.

   :param minusY: Souřadnice Y v S-JTSK (záporná hodnota; typicky v rozmezí -905000 až -400000 m).
   :param minusX: Souřadnice X v S-JTSK (záporná hodnota; typicky v rozmezí -1230000 až -930000 m).
   :param height: Výška nad elipsoidem v metrech (výchozí 0).

       :return: Vrací seznam.
       :raises Exception: Vyvolá se při splnění podmínky ``minusY < -905000 or minusY > -400000 or minusX < -1230000 or (minusX > -930000)``.

.. py:function:: wgs84_to_bessel(latitude, longitude, altitude)

   Převede geodetické souřadnice z elipsoidu WGS-84 na Besselův elipsoid.

   :param latitude: Zeměpisná šířka ve stupních (WGS-84).
   :param longitude: Zeměpisná délka ve stupních (WGS-84).
   :param altitude: Výška nad elipsoidem WGS-84 v metrech (výchozí 0.0).

       :return: Vrací seznam.

.. py:function:: bessel_to_wgs84(latitude, longitude, altitude)

   Převede geodetické souřadnice z Besselova elipsoidu na elipsoid WGS-84.

   :param latitude: Zeměpisná šířka ve stupních (Besselův elipsoid).
   :param longitude: Zeměpisná délka ve stupních (Besselův elipsoid).
   :param altitude: Výška nad Besselovým elipsoidem v metrech (výchozí 0.0).

       :return: Vrací seznam.

.. py:function:: bessel_to_jtsk(B, L)

   Převede geodetické souřadnice z Besselova elipsoidu do souřadnic S-JTSK05.

   :param B: Zeměpisná šířka ve stupních na Besselově elipsoidu.
   :param L: Zeměpisná délka ve stupních na Besselově elipsoidu.

       :return: Vrací seznam.

.. py:function:: jtsk_to_bessel(X05, Y05)

   Převede souřadnice S-JTSK05 na geodetické souřadnice Besselova elipsoidu.

   :param X05: Souřadnice X v S-JTSK05 (vč. offsetu 5 000 000 m).
   :param Y05: Souřadnice Y v S-JTSK05 (vč. offsetu 5 000 000 m).

       :return: Vrací seznam.

.. py:function:: blht_to_geo_coords_wgs(b, l, h)

   Převede geodetické souřadnice (B, L, H) na kartézské souřadnice (X, Y, Z) na elipsoidu WGS-84.

   :param b: Zeměpisná šířka v radiánech (WGS-84).
   :param l: Zeměpisná délka v radiánech (WGS-84).
   :param h: Výška nad elipsoidem v metrech.

       :return: Vrací seznam.

.. py:function:: blht_to_geo_coords_bessel(b, l, h)

   Převede geodetické souřadnice (B, L, H) na kartézské souřadnice (X, Y, Z) na Besselově elipsoidu.

   :param b: Zeměpisná šířka v radiánech (Besselův elipsoid).
   :param l: Zeměpisná délka v radiánech (Besselův elipsoid).
   :param h: Výška nad elipsoidem v metrech.

       :return: Vrací seznam.

.. py:function:: geo_coords_to_blh_bessel(X, Y, Z)

   Převede kartézské souřadnice (X, Y, Z) na geodetické souřadnice (B, L, H) na Besselově elipsoidu.

   :param X: Kartézská souřadnice X v metrech.
   :param Y: Kartézská souřadnice Y v metrech.
   :param Z: Kartézská souřadnice Z v metrech.

       :return: Vrací seznam.

.. py:function:: geo_coords_to_blh_wgs(X, Y, Z)

   Převede kartézské souřadnice (X, Y, Z) na geodetické souřadnice (B, L, H) na elipsoidu WGS-84.

   :param X: Kartézská souřadnice X v metrech.
   :param Y: Kartézská souřadnice Y v metrech.
   :param Z: Kartézská souřadnice Z v metrech.

       :return: Vrací seznam.

.. py:function:: ETRF2JTSK05transform_coords(xs, ys, zs)

   Transformuje kartézské souřadnice z ETRF89 do S-JTSK05 pomocí 7-parametrové Helmertovy transformace.

   :param xs: Kartézská souřadnice X ve vstupním systému ETRF89 v metrech.
   :param ys: Kartézská souřadnice Y ve vstupním systému ETRF89 v metrech.
   :param zs: Kartézská souřadnice Z ve vstupním systému ETRF89 v metrech.

       :return: Vrací seznam.

.. py:function:: JTSK052ETRFtransform_coords(xs, ys, zs)

   Transformuje kartézské souřadnice ze S-JTSK05 do ETRF89 pomocí 7-parametrové Helmertovy transformace.

   :param xs: Kartézská souřadnice X ve vstupním systému S-JTSK05 v metrech.
   :param ys: Kartézská souřadnice Y ve vstupním systému S-JTSK05 v metrech.
   :param zs: Kartézská souřadnice Z ve vstupním systému S-JTSK05 v metrech.

       :return: Vrací seznam.

.. py:function:: WGS2ETRFtransform_coords(xs, ys, zs)

   Transformuje kartézské souřadnice z WGS-84 do ETRF89 s časově závislou korekci pohybu eurasijské desky.

   :param xs: Kartézská souřadnice X ve vstupním systému WGS-84 v metrech.
   :param ys: Kartézská souřadnice Y ve vstupním systému WGS-84 v metrech.
   :param zs: Kartézská souřadnice Z ve vstupním systému WGS-84 v metrech.

       :return: Vrací seznam.

.. py:function:: ETRF2WGStransform_coords(xs, ys, zs)

   Transformuje kartézské souřadnice z ETRF89 do WGS-84 s časově závislou korekcí pohybu eurasijské desky.

   :param xs: Kartézská souřadnice X ve vstupním systému ETRF89 v metrech.
   :param ys: Kartézská souřadnice Y ve vstupním systému ETRF89 v metrech.
   :param zs: Kartézská souřadnice Z ve vstupním systému ETRF89 v metrech.

       :return: Vrací seznam.

.. py:function:: jtsk05_to_jtsk(x05, y05)

   Převede souřadnice ze S-JTSK05 (s offsetem 5 000 000 m) do klasického S-JTSK pomocí interpolace z korekční tabulky.

   :param x05: Souřadnice X v S-JTSK05 (vč. offsetu 5 000 000 m).
   :param y05: Souřadnice Y v S-JTSK05 (vč. offsetu 5 000 000 m).

       :return: Vrací seznam.

.. py:function:: jtsk_to_jtsk05(X, Y)

   Převede souřadnice z klasického S-JTSK do S-JTSK05 (s offsetem 5 000 000 m) pomocí korekční tabulky.

   :param X: Souřadnice X v S-JTSK v metrech (bez offsetu).
   :param Y: Souřadnice Y v S-JTSK v metrech (bez offsetu).

       :return: Vrací seznam.

.. py:function:: get_multi_transform_to_sjtsk(wgs_points)

   Vrací multi transform to sjtsk.

   :param wgs_points: Seznam dvojic [zeměpisná délka, zeměpisná šířka] ve WGS-84 určených k hromadné transformaci.

       :return: Vrací proměnná ``my``.

.. py:function:: get_multi_transform_to_wgs84(jtsk_points)

   Vrací multi transform to wgs84.

   :param jtsk_points: Seznam dvojic [souřadnice Y, souřadnice X] v S-JTSK určených k hromadné transformaci.

       :return: Vrací proměnná ``my``.

.. py:function:: contains_two_floats(text)

   Ověří, zda řetězec obsahuje právě dvě desetinná čísla oddělená mezerou (formát souřadnic).

   :param text: Textový řetězec, jehož formát se ověřuje.

       :return: Vrací výsledek volání ``bool()``.

.. py:function:: transform_geom(geom, transFunc)

   Transformuje geom. v aplikaci.

   :param geom: Parametr ``geom`` předává se do volání ``isinstance()``, pracuje se s atributy ``find``, ``replace``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param transFunc: Funkce přijímající dvojici souřadnic (float, float) a vracející transformovanou dvojici.

       :return: Vrací n-tici.

.. py:function:: transform_geom_to_sjtsk(geom)

   Transformuje geom to sjtsk.

   :param geom: Parametr ``geom`` předává se do volání ``transform_geom()``, vstupuje do návratové hodnoty.

       :return: Vrací výsledek volání ``transform_geom()``.

.. py:function:: transform_geom_to_wgs84(geom)

   Transformuje geom to wgs84.

   :param geom: Parametr ``geom`` předává se do volání ``transform_geom()``, vstupuje do návratové hodnoty.

       :return: Vrací výsledek volání ``transform_geom()``.
