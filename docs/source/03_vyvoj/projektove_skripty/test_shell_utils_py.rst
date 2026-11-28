Skript test_shell_utils.py
==========================

Automaticky generovaná dokumentace skriptu ``scripts/test_shell_utils.py``.

Přehled modulu
--------------

Společné nalezení Bashe pro izolované shellové regrese.

Funkce
------

.. py:function:: bash_executable()

   Najde Git Bash vůči instalaci Gitu, jinak použije Bash z PATH.

   :return: Cesta k interpretu nebo ``None``; spouštěč WSL není Bash pro tyto testy.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_shell_utils.py
   :language: python
   :linenos:
