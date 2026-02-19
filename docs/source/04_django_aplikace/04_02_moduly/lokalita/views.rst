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

   .. py:method:: rename_field_for_ordering()

   .. py:method:: get_queryset()

   .. py:method:: get_context_data()


.. py:class:: LokalitaDetailView

   Třida pohledu pro zobrazení detailu lokality.

   **Metody:**

   .. py:method:: get()

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získaní akce z db.

   .. py:method:: check_locality_arch_z_conflict()

   .. py:method:: get_context_data()

      Metoda pro získaní contextu akci pro template.

   .. py:method:: get_shows()


.. py:class:: LokalitaCreateView

   Třida pohledu pro vytvoření lokality.

   **Metody:**

   .. py:method:: get_context_data()

   .. py:method:: form_valid()

   .. py:method:: form_invalid()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: LokalitaEditView

   Třida pohledu pro editaci lokality.

   **Metody:**

   .. py:method:: get_context_data()

   .. py:method:: form_valid()

   .. py:method:: form_invalid()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: LokalitaRelatedView

   Třida pohledu pro získaní relací lokality, která je dedená v dalších pohledech.


.. py:class:: LokalitaDokumentacniJednotkaCreateView

   Třida pohledu pro vytvoření dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()


.. py:class:: LokalitaDokumentacniJednotkaRelatedView

   Třida pohledu pro získaní dokumentačních jednotek lokality, která je dedená v dalších pohledech.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: get_dokumentacni_jednotka()

   .. py:method:: get_context_data()


.. py:class:: LokalitaDokumentacniJednotkaUpdateView

   Třida pohledu pro editaci dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()


.. py:class:: LokalitaKomponentaCreateView

   Třida pohledu pro vytvoření komponenty lokality.

   **Metody:**

   .. py:method:: get_context_data()

   .. py:method:: get()


.. py:class:: LokalitaKomponentaUpdateView

   Třida pohledu pro editaci komponenty lokality.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: get_komponenta()

   .. py:method:: get_context_data()


.. py:class:: LokalitaPianCreateView

   Třida pohledu pro vytvoření pianu dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

   .. py:method:: get()


.. py:class:: LokalitaPianUpdateView

   Třida pohledu pro editaci pianu dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: get_pian()

   .. py:method:: get_context_data()

   .. py:method:: get()


Funkce
------

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu lokality.


   **Argumenty:**

   - ``zaznam`` (*Lokalita*): model Lokalita pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.
