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

      :param char: Číselná nebo geometrická hodnota `char` použitá při výpočtu nebo transformaci.
      :param chunk_size: Číselná nebo geometrická hodnota `chunk_size` použitá při výpočtu nebo transformaci.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _convert_text()

      Převede text.

      :param text: Číselná hodnota ``text`` použitá při výpočtu nebo transformaci.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _format_akce_str()

      Provádí operaci format akce str.

      :param akce: Doménový objekt `akce`, se kterým funkce pracuje.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _format_akce()

      Provádí operaci format akce.

      :param akce_all: Doménový objekt `akce_all`, se kterým funkce pracuje.
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

      :param name: Název nebo identifikátor používaný v rámci operace.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param projekt: Doménový objekt `projekt`, se kterým funkce pracuje.
      :param popup_parametry: Číselná hodnota ``popup_parametry`` použitá při výpočtu nebo transformaci.

