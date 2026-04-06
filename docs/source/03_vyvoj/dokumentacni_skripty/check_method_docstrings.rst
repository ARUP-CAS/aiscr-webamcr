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

      :param node: AST uzel definice třídy.

   .. py:method:: visit_FunctionDef()

      Zpracuje běžnou definici funkce nebo metody.

      :param node: AST uzel definice funkce.

   .. py:method:: visit_AsyncFunctionDef()

      Zpracuje asynchronní definici funkce nebo metody.

      :param node: AST uzel asynchronní definice funkce.

   .. py:method:: _handle_function_like()

   .. py:method:: _should_skip()

   .. py:method:: _collect_args()

   .. py:method:: _has_meaningful_return()

   .. py:method:: _check_docstring()


Funkce
------

.. py:function:: env_flag(name, default)

   Vyhodnotí hodnotu proměnné prostředí jako booleovský příznak.

   :param name: Název proměnné prostředí.
   :param default: Výchozí hodnota použitá při neexistenci proměnné.
   :return: ```True```, pokud hodnota odpovídá pravdivému příznaku.

.. py:function:: iter_python_files(paths, bypass_exclusions)

   Iteruje Python soubory ve vstupních cestách.

   :param paths: Seznam souborů nebo adresářů ke kontrole.
   :param bypass_exclusions: Pokud ``True``, nepoužije se filtr ignorovaných adresářů.
   :return: Generátor cest k nalezeným ```.py``` souborům.

.. py:function:: main()

   Spustí kontrolu docstringů nad zadanými Python soubory.

   :return: Návratový kód procesu (0 při úspěchu, jinak 1 ve strict režimu).
