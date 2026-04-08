PROJEKT doc_utils
=================

Modul doc_utils.

Třídy
------

.. py:class:: DocumentCreator

   Implementuje komponentu ``DocumentCreator`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param oznamovatel: Uživatel nebo osoba `oznamovatel`, v jejímž kontextu se operace provádí.
      :param projekt: Parametr ``projekt`` slouží jako vstup pro logiku funkce ``__init__``.
      :param fedora_transaction: Parametr ``fedora_transaction`` slouží jako vstup pro logiku funkce ``__init__``.
      :param additional: Kolekce nebo datová struktura `additional` zpracovávaná touto funkcí.

   .. py:method:: format_date()

             Provádí operaci format date.

      :param date_obj: Časový údaj ``date_obj`` použitý při filtrování nebo výpočtu.
      Zpracovaná hodnota po validaci nebo transformaci.

      :return: Vrací hodnotu typu ``str``; podle větve může jít o: str, výsledek volání ``strftime()``.

   .. py:method:: _create_style_dict()

      Vytvoří style dict.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_header_oznamovatel()

      Vytvoří header oznamovatel.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_header_oznamovatel_doc()

      Vytvoří header oznamovatel doc.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_header_tab_dates()

      Vytvoří header tab dates.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_header_tab_dates_doc()

      Vytvoří header tab dates doc.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_data_document_part()

      Vytvoří data document part.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_signature()

      Vytvoří signature.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_signature_doc()

      Vytvoří signature doc.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _initiate_document()

             Provádí operaci initiate document.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _generate_repository_file()

      Vygeneruje repository file.

      :param my_doc: Číselná hodnota ``my_doc`` použitá při výpočtu nebo transformaci.
      :param document_content: Textový nebo strukturální vstup `document_content` používaný při sestavení nebo zpracování obsahu.
      :param pdf_buffer: Číselná hodnota ``pdf_buffer`` použitá při výpočtu nebo transformaci.
      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: body_style()

      Provádí operaci body style.

      :return: Vrací vybranou hodnotu z kolekce.

   .. py:method:: _generate_text()

      Vygeneruje text.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.


.. py:class:: OznameniPDFCreator

   Implementuje komponentu ``OznameniPDFCreator`` v rámci aplikace.

   **Metody:**

   .. py:method:: _generate_text()

      Vygeneruje text.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      :return: Nově vytvořená hodnota připravená touto funkcí.


.. py:class:: ZruseniPDFCreator

   Implementuje komponentu ``ZruseniPDFCreator`` v rámci aplikace.

   **Metody:**

   .. py:method:: _generate_text()

      Vygeneruje text.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      :return: Nově vytvořená hodnota připravená touto funkcí.


Funkce
------

.. py:function:: draw_image(filename, canvas, counter)

   Vykreslí obrázek na ReportLab canvas na pozici určenou pořadovým číslem (vlevo, uprostřed, vpravo).

   :param filename: Cesta k souboru obrázku, který se vykreslí do záhlaví.
   :param canvas: ReportLab canvas objekt, na který se obrázek nakreslí.
   :param counter: Pořadové číslo obrázku (0 = vlevo, 1 = uprostřed, 2 = vpravo).

.. py:function:: add_page_number(canvas, doc)

   Provádí operaci add page number.

   :param canvas: Parametr ``canvas`` pracuje se s atributy ``saveState``, ``setFont``.
   :param doc: Objekt dokumentu, který je funkcí upravován nebo čten.

.. py:function:: draw_header(canvas, doc)

   Provádí operaci draw header.

   :param canvas: Parametr ``canvas`` předává se do volání ``draw_image()``, ``add_page_number()``.
   :param doc: Objekt dokumentu, který je funkcí upravován nebo čten.
