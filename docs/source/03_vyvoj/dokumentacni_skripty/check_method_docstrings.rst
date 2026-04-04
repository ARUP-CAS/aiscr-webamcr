Skript check_method_docstrings
==============================

Dokumentace skriptu ``docs/check_method_docstrings.py``.

Přehled modulu
--------------

Kontrola docstringů tříd, metod a funkcí dle projektového style guide.

Třídy
------

.. py:class:: MethodDocstringChecker

   AST návštěvník, který kontroluje přítomnost a kvalitu docstringů.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: visit_ClassDef()

      Zkontroluje docstring třídy a navštíví její potomky.

      **Parametry:**

      - ``node``: AST uzel definice třídy.


   .. py:method:: visit_FunctionDef()

      Zpracuje běžnou definici funkce nebo metody.

      **Parametry:**

      - ``node``: AST uzel definice funkce.


   .. py:method:: visit_AsyncFunctionDef()

      Zpracuje asynchronní definici funkce nebo metody.

      **Parametry:**

      - ``node``: AST uzel asynchronní definice funkce.


   .. py:method:: _handle_function_like()

   .. py:method:: _should_skip()

   .. py:method:: _collect_args()

   .. py:method:: _has_meaningful_return()

   .. py:method:: _check_docstring()


Funkce
------

.. py:function:: env_flag(name, default)

   Vyhodnotí hodnotu proměnné prostředí jako booleovský příznak.

   **Parametry:**

   - ``name``: Název proměnné prostředí.
   - ``default``: Výchozí hodnota použitá při neexistenci proměnné.

   **Návratová hodnota:**

   ```True```, pokud hodnota odpovídá pravdivému příznaku.


.. py:function:: iter_python_files(paths, bypass_exclusions)

   Iteruje Python soubory ve vstupních cestách.

   **Parametry:**

   - ``paths``: Seznam souborů nebo adresářů ke kontrole.
   - ``bypass_exclusions``: Pokud ``True``, nepoužije se filtr ignorovaných adresářů.

   **Návratová hodnota:**

   Generátor cest k nalezeným ```.py``` souborům.


.. py:function:: main()

   Spustí kontrolu docstringů nad zadanými Python soubory.

   **Návratová hodnota:**

   Návratový kód procesu (0 při úspěchu, jinak 1 ve strict režimu).

