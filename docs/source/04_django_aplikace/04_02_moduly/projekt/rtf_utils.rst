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

      :param char: Parametr ``char`` pracuje se s atributy ``encode``.
      :param chunk_size: Parametr ``chunk_size`` se předává do volání ``range()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _convert_text()

             Převede text.

      :param text: Číselná hodnota ``text`` použitá při výpočtu nebo transformaci.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _format_akce_str()

             Provádí operaci format akce str.

      :param akce: Parametr ``akce`` předává se do volání ``str()``, pracuje se s atributy ``hlavni_typ``, ``vedlejsi_typ``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _format_akce()

             Provádí operaci format akce.

      :param akce_all: Parametr ``akce_all`` pracuje se s atributy ``count``, ovlivňuje větvení podmínek.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_vysledek_text()

      Vrací vysledek text.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_typ_vyzkumu_text()

      Vrací typ vyzkumu text.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _generate_text()

      Vygeneruje text.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _open_file()

             Provádí operaci open file.

      :param name: Parametr ``name`` předává se do volání ``open()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param projekt: Parametr ``projekt`` slouží jako vstup pro logiku funkce ``__init__``.
      :param popup_parametry: Číselná hodnota ``popup_parametry`` použitá při výpočtu nebo transformaci.

