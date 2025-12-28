PROJEKT formuláře
=================

Definice formulářů.

Třídy
------

.. py:class:: CreateProjektForm

   Hlavní formulář pro vytvoření projektu.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: clean()


.. py:class:: EditProjektForm

   Hlavní formulář pro editaci projektu.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: clean()

      Kontrola datumu zahájení a ukončení pri validaci formuláře.


.. py:class:: NavrhnoutZruseniProjektForm

   Formulář pro navržení zrušení projektu.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: clean()

      Metoda na kontrolu obsahu důvodu pro zrušení.


.. py:class:: PrihlaseniProjektForm

   Hlavní formulář pro prihlášení projektu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ZahajitVTerenuForm

   Formulář pro zahájení projektu v terénu.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: clean()


.. py:class:: UkoncitVTerenuForm

   Formulář pro ukončení projektu v terénu.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: clean()

      Metoda pro kontrolu datumu ukončení.


.. py:class:: ZruseniProjektForm

   Formulář pro zrušení projektu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: GenerovatNovePotvrzeniForm

   Formulář pro vygenerování nového potvrzení projektu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: GenerovatExpertniListForm

   Formulář pro generování expertního listu projektu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: PripojitProjektForm

   Formulář pro pripojení projektu do akce nebo dokumentu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: ProjektFilterForm

   Popis není k dispozici.


.. py:class:: ZadostProjektForm

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: UpravitDatumOznameniForm

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: NeodeslatMailForm

   Formulář neodeslání mailu oznamovateli.

   **Metody:**

   .. py:method:: __init__()

