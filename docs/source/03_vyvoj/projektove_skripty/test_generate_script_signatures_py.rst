Skript test_generate_script_signatures.py
=========================================

Automaticky generovaná dokumentace skriptu ``scripts/test_generate_script_signatures.py``.

Přehled modulu
--------------

Regrese signatur funkcí, které generátor dokumentace vypisuje na stránkách skriptů.

Třídy
------

.. py:class:: ScriptSignatureTests

   Ověří, že signatura zachová všechny druhy parametrů funkce v jejich pořadí.

   **Metody:**

   .. py:method:: test_signatures_keep_every_parameter_kind()

      Poziční, ``*args``, pouze pojmenované a ``**kwargs`` parametry zůstanou v signatuře.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_generate_script_signatures.py
   :language: python
   :linenos:
