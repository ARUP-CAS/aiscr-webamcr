PIAN formuláře
==============

Definice formulářů.

Třídy
------

.. py:class:: PianCreateForm

   Hlavní formulář pro vytvoření, editaci a zobrazení pianu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param dj: Volitelná instance dokumentační jednotky pro secondary lock — sleduje
          souběžné změny polí DJ, které by mohly být přepsány při ``dj.save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: get_dj_conflicting_fields()

      Vrátí seznam polí DJ, která byla v DB změněna od renderu formuláře.

      :return: Seznam názvů polí (``typ``, ``nazev``, ``negativni_jednotka``, ``pian``).

   .. py:method:: _instance_geom_wkt()

             Provádí operaci instance geom wkt.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: run_loaded_validation()

      Metoda pro validaci geometrií při potvrzení PIANu.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: clean()

      Provádí operaci clean.

      :raises forms.ValidationError: Vyvolá se při splnění podmínky ``isinstance(geom, Polygon)``; nebo při splnění podmínky ``zm10 is not None and zm50 is not None``.

   .. py:method:: validate_geom()

      Metoda pro validaci PIAN pomocí funkce v postgres databázi.

      :param geom: Parametr ``geom`` předává se do volání ``callproc()``, ``debug()``.
      :param epsg: Parametr ``epsg`` se předává do volání ``callproc()``.

      :raises forms.ValidationError: Vyvolá se při zpracování zachycené výjimky typu ``Exception``; nebo při splnění podmínky ``validation_results != 'valid'``.


.. py:class:: PianOdpojitForm

   Minimální formulář pro modál odpojení PIANu od DJ.

   Nese pouze secondary lock proti instanci DJ, aby šlo detekovat souběžnou editaci
   polí DJ (např. ``typ``) předtím, než je v ``pian/views.py:odpojit`` zavolán
   ``dj.save()``.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář se snapshotem polí DJ.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param dj: Volitelná instance dokumentační jednotky pro secondary lock.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: get_dj_conflicting_fields()

      Vrátí seznam polí DJ, která byla v DB změněna od renderu formuláře.

      :return: Seznam názvů polí (``typ``, ``nazev``, ``negativni_jednotka``, ``pian``).

