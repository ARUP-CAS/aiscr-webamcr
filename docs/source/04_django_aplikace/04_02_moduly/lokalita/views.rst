LOKALITA views
==============

Definice views.

Třídy
------

.. py:class:: LokalitaIndexView

   Třida pohledu pro zobrazení domovské stránky lokalit s navigačními možnostmi.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaListView

   Třida pohledu pro zobrazení listu/tabulky s lokalitami.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Záznam/objekt ``field``, který funkce čte, validuje nebo upravuje.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaDetailView

   Třida pohledu pro zobrazení detailu lokality.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získaní akce z db.

   .. py:method:: check_locality_arch_z_conflict()

      Ověří locality arch z conflict.

   .. py:method:: get_context_data()

      Metoda pro získaní contextu akci pro template.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_shows()

      Vrací shows. v aplikaci.


.. py:class:: LokalitaCreateView

   Třida pohledu pro vytvoření lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaEditView

   Třida pohledu pro editaci lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaRelatedView

   Třida pohledu pro získaní relací lokality, která je dedená v dalších pohledech.


.. py:class:: LokalitaDokumentacniJednotkaCreateView

   Třida pohledu pro vytvoření dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaDokumentacniJednotkaRelatedView

   Třida pohledu pro získaní dokumentačních jednotek lokality, která je dedená v dalších pohledech.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_dokumentacni_jednotka()

      Vrací dokumentacni jednotka.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaDokumentacniJednotkaUpdateView

   Třida pohledu pro editaci dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaKomponentaCreateView

   Třida pohledu pro vytvoření komponenty lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaKomponentaUpdateView

   Třida pohledu pro editaci komponenty lokality.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_komponenta()

      Vrací komponenta. v aplikaci.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaPianCreateView

   Třida pohledu pro vytvoření pianu dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaPianUpdateView

   Třida pohledu pro editaci pianu dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_pian()

      Vrací pian. v aplikaci.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


Funkce
------

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu lokality.

   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.
