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

      **Parametry:**

      - ``oznamovatel``: Uživatel nebo osoba `oznamovatel`, v jejímž kontextu se operace provádí.
      - ``projekt``: Parametr ``projekt`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``fedora_transaction``: Parametr ``fedora_transaction`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``additional``: Kolekce nebo datová struktura `additional` zpracovávaná touto funkcí.


   .. py:method:: format_date()

      Provádí operaci format date.

      **Parametry:**

      - ``date_obj``: Časový údaj ``date_obj`` použitý při filtrování nebo výpočtu.

      **Návratová hodnota:**

      Vrací hodnotu typu ``str``; podle větve může jít o: str, výsledek volání ``strftime()``.

      Zpracovaná hodnota po validaci nebo transformaci.

   .. py:method:: _create_style_dict()

      Vytvoří style dict.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_header_oznamovatel()

      Vytvoří header oznamovatel.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_header_oznamovatel_doc()

      Vytvoří header oznamovatel doc.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_header_tab_dates()

      Vytvoří header tab dates.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_header_tab_dates_doc()

      Vytvoří header tab dates doc.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_data_document_part()

      Vytvoří data document part.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_signature()

      Vytvoří signature.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_signature_doc()

      Vytvoří signature doc.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _initiate_document()

      Provádí operaci initiate document.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _generate_repository_file()

      Vygeneruje repository file.

      **Parametry:**

      - ``my_doc``: Číselná hodnota ``my_doc`` použitá při výpočtu nebo transformaci.
      - ``document_content``: Textový nebo strukturální vstup `document_content` používaný při sestavení nebo zpracování obsahu.
      - ``pdf_buffer``: Číselná hodnota ``pdf_buffer`` použitá při výpočtu nebo transformaci.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: body_style()

      Provádí operaci body style.

      **Návratová hodnota:**

      Vrací vybranou hodnotu z kolekce.


   .. py:method:: _generate_text()

      Vygeneruje text.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: build_document()

      Sestaví document. v aplikaci.


.. py:class:: OznameniPDFCreator

   Implementuje komponentu ``OznameniPDFCreator`` v rámci aplikace.

   **Metody:**

   .. py:method:: _generate_text()

      Vygeneruje text.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.



.. py:class:: ZruseniPDFCreator

   Implementuje komponentu ``ZruseniPDFCreator`` v rámci aplikace.

   **Metody:**

   .. py:method:: _generate_text()

      Vygeneruje text.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.



Funkce
------

.. py:function:: draw_image(filename, canvas, counter)

   Vykreslí obrázek na ReportLab canvas na pozici určenou pořadovým číslem (vlevo, uprostřed, vpravo).

   **Parametry:**

   - ``filename``: Cesta k souboru obrázku, který se vykreslí do záhlaví.
   - ``canvas``: ReportLab canvas objekt, na který se obrázek nakreslí.
   - ``counter``: Pořadové číslo obrázku (0 = vlevo, 1 = uprostřed, 2 = vpravo).


.. py:function:: add_page_number(canvas, doc)

   Provádí operaci add page number.

   **Parametry:**

   - ``canvas``: Parametr ``canvas`` pracuje se s atributy ``saveState``, ``setFont``.
   - ``doc``: Objekt dokumentu, který je funkcí upravován nebo čten.


.. py:function:: draw_header(canvas, doc)

   Provádí operaci draw header.

   **Parametry:**

   - ``canvas``: Parametr ``canvas`` předává se do volání ``draw_image()``, ``add_page_number()``.
   - ``doc``: Objekt dokumentu, který je funkcí upravován nebo čten.

