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

      :param oznamovatel: Vstupní hodnota ``oznamovatel`` pro danou operaci.
      :param projekt: Vstupní hodnota ``projekt`` pro danou operaci.
      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :param additional: Vstupní hodnota ``additional`` pro danou operaci.

   .. py:method:: format_date()

      Provádí operaci format date.

      :param date_obj: Vstupní hodnota ``date_obj`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _create_style_dict()

      Vytvoří style dict.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_header_oznamovatel()

      Vytvoří header oznamovatel.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_header_oznamovatel_doc()

      Vytvoří header oznamovatel doc.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_header_tab_dates()

      Vytvoří header tab dates.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_header_tab_dates_doc()

      Vytvoří header tab dates doc.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_data_document_part()

      Vytvoří data document part.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_signature()

      Vytvoří signature.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_signature_doc()

      Vytvoří signature doc.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _initiate_document()

      Provádí operaci initiate document.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _generate_repository_file()

      Vygeneruje repository file.

      :param my_doc: Vstupní hodnota ``my_doc`` pro danou operaci.
      :param document_content: Vstupní hodnota ``document_content`` pro danou operaci.
      :param pdf_buffer: Vstupní hodnota ``pdf_buffer`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: body_style()

      Provádí operaci body style.

   .. py:method:: _generate_text()

      Vygeneruje text.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.


.. py:class:: OznameniPDFCreator

   Implementuje komponentu ``OznameniPDFCreator`` v rámci aplikace.

   **Metody:**

   .. py:method:: _generate_text()

      Vygeneruje text.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      :return: Vrací nově vytvořený výsledek operace.


.. py:class:: ZruseniPDFCreator

   Implementuje komponentu ``ZruseniPDFCreator`` v rámci aplikace.

   **Metody:**

   .. py:method:: _generate_text()

      Vygeneruje text.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: build_document()

      Sestaví document. v aplikaci.

      :return: Vrací nově vytvořený výsledek operace.


Funkce
------

.. py:function:: draw_image(filename, canvas, counter)

   Provádí operaci draw image.

   :param filename: Vstupní hodnota ``filename`` pro danou operaci.
   :param canvas: Vstupní hodnota ``canvas`` pro danou operaci.
   :param counter: Vstupní hodnota ``counter`` pro danou operaci.

.. py:function:: add_page_number(canvas, doc)

   Provádí operaci add page number.

   :param canvas: Vstupní hodnota ``canvas`` pro danou operaci.
   :param doc: Vstupní hodnota ``doc`` pro danou operaci.

.. py:function:: draw_header(canvas, doc)

   Provádí operaci draw header.

   :param canvas: Vstupní hodnota ``canvas`` pro danou operaci.
   :param doc: Vstupní hodnota ``doc`` pro danou operaci.
