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

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: _instance_geom_wkt()

      Provádí operaci instance geom wkt.

      **Parametry:**

      - ``field_name``: Textový název nebo klíč ``field_name`` používaný v rámci operace.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: run_loaded_validation()

      Metoda pro validaci geometrií při potvrzení PIANu.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: clean()

      Provádí operaci clean.

      **Výjimky:**

      - ``forms.ValidationError``: Vyvolá se při splnění podmínky ``isinstance(geom, Polygon)``; nebo při splnění podmínky ``zm10 is not None and zm50 is not None``.


   .. py:method:: validate_geom()

      Metoda pro validaci PIAN pomocí funkce v postgres databázi.

      **Parametry:**

      - ``geom``: Parametr ``geom`` předává se do volání ``callproc()``, ``debug()``.
      - ``epsg``: Parametr ``epsg`` se předává do volání ``callproc()``.

      **Výjimky:**

      - ``forms.ValidationError``: Vyvolá se při zpracování zachycené výjimky typu ``Exception``; nebo při splnění podmínky ``validation_results != 'valid'``.


