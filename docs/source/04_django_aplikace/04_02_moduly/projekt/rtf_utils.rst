PROJEKT rtf_utils
=================

Modul rtf_utils.

Třídy
------

.. py:class:: ExpertniListCreator

   Implementuje komponentu ``ExpertniListCreator`` v rámci aplikace.

   **Metody:**

   .. py:method:: _utf16_decimals()

      Provádí operaci utf16 decimals.

      **Parametry:**

      - ``char``: Parametr ``char`` pracuje se s atributy ``encode``.
      - ``chunk_size``: Parametr ``chunk_size`` se předává do volání ``range()``.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _convert_text()

      Převede text.

      **Parametry:**

      - ``text``: Číselná hodnota ``text`` použitá při výpočtu nebo transformaci.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _format_akce_str()

      Provádí operaci format akce str.

      **Parametry:**

      - ``akce``: Parametr ``akce`` předává se do volání ``str()``, pracuje se s atributy ``hlavni_typ``, ``vedlejsi_typ``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _format_akce()

      Provádí operaci format akce.

      **Parametry:**

      - ``akce_all``: Parametr ``akce_all`` pracuje se s atributy ``count``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _get_vysledek_text()

      Vrací vysledek text.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_typ_vyzkumu_text()

      Vrací typ vyzkumu text.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _generate_text()

      Vygeneruje text.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _open_file()

      Provádí operaci open file.

      **Parametry:**

      - ``name``: Parametr ``name`` předává se do volání ``open()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``projekt``: Parametr ``projekt`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``popup_parametry``: Číselná hodnota ``popup_parametry`` použitá při výpočtu nebo transformaci.


