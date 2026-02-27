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


.. py:class:: LokalitaListView

   Třida pohledu pro zobrazení listu/tabulky s lokalitami.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Vstupní hodnota ``field`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaDetailView

   Třida pohledu pro zobrazení detailu lokality.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získaní akce z db.

   .. py:method:: check_locality_arch_z_conflict()

      Ověří locality arch z conflict.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: get_context_data()

      Metoda pro získaní contextu akci pro template.

   .. py:method:: get_shows()

      Vrací shows.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaCreateView

   Třida pohledu pro vytvoření lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: LokalitaEditView

   Třida pohledu pro editaci lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: LokalitaRelatedView

   Třida pohledu pro získaní relací lokality, která je dedená v dalších pohledech.


.. py:class:: LokalitaDokumentacniJednotkaCreateView

   Třida pohledu pro vytvoření dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaDokumentacniJednotkaRelatedView

   Třida pohledu pro získaní dokumentačních jednotek lokality, která je dedená v dalších pohledech.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_dokumentacni_jednotka()

      Vrací dokumentacni jednotka.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaDokumentacniJednotkaUpdateView

   Třida pohledu pro editaci dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaKomponentaCreateView

   Třida pohledu pro vytvoření komponenty lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaKomponentaUpdateView

   Třida pohledu pro editaci komponenty lokality.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_komponenta()

      Vrací komponenta.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaPianCreateView

   Třida pohledu pro vytvoření pianu dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaPianUpdateView

   Třida pohledu pro editaci pianu dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_pian()

      Vrací pian.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu lokality.


   **Argumenty:**

   - ``zaznam`` (*Lokalita*): model Lokalita pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.
