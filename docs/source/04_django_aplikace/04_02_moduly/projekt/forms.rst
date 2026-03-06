PROJEKT formuláře
=================

Definice formulářů.

Třídy
------

.. py:class:: CreateProjektForm

   Hlavní formulář pro vytvoření projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: clean()

      Provádí operaci clean.


.. py:class:: EditProjektForm

   Hlavní formulář pro editaci projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param edit_fields: Záznam/objekt ``edit_fields``, který funkce čte, validuje nebo upravuje.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: clean()

      Kontrola datumu zahájení a ukončení pri validaci formuláře.


.. py:class:: NavrhnoutZruseniProjektForm

   Formulář pro navržení zrušení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: clean()

      Metoda na kontrolu obsahu důvodu pro zrušení.


.. py:class:: PrihlaseniProjektForm

   Hlavní formulář pro prihlášení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ZahajitVTerenuForm

   Formulář pro zahájení projektu v terénu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: clean()

      Provádí operaci clean.


.. py:class:: UkoncitVTerenuForm

   Formulář pro ukončení projektu v terénu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: clean()

      Metoda pro kontrolu datumu ukončení.


.. py:class:: ZruseniProjektForm

   Formulář pro zrušení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: GenerovatNovePotvrzeniForm

   Formulář pro vygenerování nového potvrzení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: GenerovatExpertniListForm

   Formulář pro generování expertního listu projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PripojitProjektForm

   Formulář pro pripojení projektu do akce nebo dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param dok: Doménový objekt `dok`, se kterým funkce pracuje.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ProjektFilterForm

   Implementuje komponentu ``ProjektFilterForm`` v rámci aplikace.


.. py:class:: ZadostProjektForm

   Implementuje komponentu ``ZadostProjektForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param label: Textový název nebo klíč ``label`` používaný v rámci operace.
      :param help_text: Číselná hodnota ``help_text`` použitá při výpočtu nebo transformaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: UpravitDatumOznameniForm

   Implementuje komponentu ``UpravitDatumOznameniForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: NeodeslatMailForm

   Formulář neodeslání mailu oznamovateli.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

