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

      :param char: Vstupní hodnota ``char`` pro danou operaci.
      :param chunk_size: Vstupní hodnota ``chunk_size`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _convert_text()

      Převede text.

      :param text: Vstupní hodnota ``text`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _format_akce_str()

      Provádí operaci format akce str.

      :param akce: Vstupní hodnota ``akce`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _format_akce()

      Provádí operaci format akce.

      :param akce_all: Vstupní hodnota ``akce_all`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_vysledek_text()

      Vrací vysledek text.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_typ_vyzkumu_text()

      Vrací typ vyzkumu text.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _generate_text()

      Vygeneruje text.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _open_file()

      Provádí operaci open file.

      :param name: Vstupní hodnota ``name`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param projekt: Vstupní hodnota ``projekt`` pro danou operaci.
      :param popup_parametry: Vstupní hodnota ``popup_parametry`` pro danou operaci.

