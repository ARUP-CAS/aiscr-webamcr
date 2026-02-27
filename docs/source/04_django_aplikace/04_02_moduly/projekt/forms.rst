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
      :param required: Vstupní hodnota ``required`` pro danou operaci.
      :param required_next: Vstupní hodnota ``required_next`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: clean()

      Provádí operaci clean.

      :return: Vrací výsledek provedené operace.


.. py:class:: EditProjektForm

   Hlavní formulář pro editaci projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param required: Vstupní hodnota ``required`` pro danou operaci.
      :param required_next: Vstupní hodnota ``required_next`` pro danou operaci.
      :param edit_fields: Vstupní hodnota ``edit_fields`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: clean()

      Kontrola datumu zahájení a ukončení pri validaci formuláře.


.. py:class:: NavrhnoutZruseniProjektForm

   Formulář pro navržení zrušení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: clean()

      Metoda na kontrolu obsahu důvodu pro zrušení.


.. py:class:: PrihlaseniProjektForm

   Hlavní formulář pro prihlášení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: ZahajitVTerenuForm

   Formulář pro zahájení projektu v terénu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: clean()

      Provádí operaci clean.

      :return: Vrací výsledek provedené operace.


.. py:class:: UkoncitVTerenuForm

   Formulář pro ukončení projektu v terénu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: clean()

      Metoda pro kontrolu datumu ukončení.


.. py:class:: ZruseniProjektForm

   Formulář pro zrušení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: GenerovatNovePotvrzeniForm

   Formulář pro vygenerování nového potvrzení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: GenerovatExpertniListForm

   Formulář pro generování expertního listu projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: PripojitProjektForm

   Formulář pro pripojení projektu do akce nebo dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param dok: Vstupní hodnota ``dok`` pro danou operaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: ProjektFilterForm

   Implementuje komponentu ``ProjektFilterForm`` v rámci aplikace.


.. py:class:: ZadostProjektForm

   Implementuje komponentu ``ZadostProjektForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param label: Vstupní hodnota ``label`` pro danou operaci.
      :param help_text: Vstupní hodnota ``help_text`` pro danou operaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: UpravitDatumOznameniForm

   Implementuje komponentu ``UpravitDatumOznameniForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: NeodeslatMailForm

   Formulář neodeslání mailu oznamovateli.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

