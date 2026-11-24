Skript check_stack_ready.py
===========================

Automaticky generovaná dokumentace skriptu ``scripts/check_stack_ready.py``.

Přehled modulu
--------------

Ověří požadované služby a skutečné zdraví kontejnerů cílového stacku.

Funkce
------

.. py:function:: docker()

   Spustí pouze čtecí Docker CLI a odmítne neúplné inspekce.

   :param args: Argumenty čtecího příkazu.
   :return: Úplný standardní výstup.

.. py:function:: expected_services(compose_files)

   Vybere názvy služeb z kanonického sloučeného výstupu Docker CLI.

   :param compose_files: Compose soubory skutečně použité k nasazení.
   :return: Neprázdná množina názvů služeb.
   :raises ValueError: Při chybějící nebo nerozpoznatelné sekci služeb.

.. py:function:: inspect_json(kind, names)

   Ověří úplnost strukturované inspekce konkrétních objektů.

   :param kind: Typ objektu Docker.
   :param names: Jednoznačně vybrané názvy nebo ID.
   :return: Seznam inspektovaných objektů.

.. py:function:: readiness(stack, services)

   Zkontroluje aktivní úlohy a zdraví pouze požadovaných služeb.

   :param stack: Přesný název cílového stacku.
   :param services: Požadované služby z Compose konfigurace.
   :return: Dvojice připravenosti a diagnostiky.

.. py:function:: wait_ready(stack, compose_files, timeout, interval)

   Počká nejvýše do stanoveného termínu; chybu inspekce neinterpretuje jako zdraví.

   :param stack: Název stacku.
   :param compose_files: Použité Compose soubory.
   :param timeout: Maximální délka čekání v sekundách.
   :param interval: Interval dalších kontrol.
   :return: Nula při připravenosti, jinak jedna.

.. py:function:: main(argv)

   Vrátí stav použitelnosti stacku pro volající nasazovací skript.

   :param argv: Volitelné argumenty CLI.
   :return: Nula při připravenosti, jinak jedna.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/check_stack_ready.py
   :language: python
   :linenos:
