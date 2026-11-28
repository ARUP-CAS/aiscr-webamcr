Skript check_stack_ready.py
===========================

Automaticky generovaná dokumentace skriptu ``scripts/check_stack_ready.py``.

Přehled modulu
--------------

Ověří požadované služby a skutečné zdraví kontejnerů cílového stacku.

Nasazovací wrappery spouštějí skript systémovým ``python3`` nasazovacího
serveru, který má Python 3.6. Skript proto smí používat jen moduly
standardní knihovny a parametry ``subprocess.run`` dostupné v Pythonu 3.6;
tuto spodní hranici hlídá ``scripts/test_pre_commit_stack_ready.py``.

Funkce
------

.. py:function:: docker(*args, deadline)

   Spustí pouze čtecí Docker CLI a odmítne neúplné inspekce.

   :param args: Argumenty čtecího příkazu.
   :param deadline: Hodnota ``time.monotonic()``, do které musí inspekce
       skončit; ``None`` omezí příkaz jen vlastním limitem 30 sekund.
   :return: Úplný standardní výstup.
   :raises TimeoutError: Pokud termín inspekce již uplynul.

.. py:function:: expected_services(compose_files, deadline)

   Vybere názvy služeb z kanonického sloučeného výstupu Docker CLI.

   :param compose_files: Compose soubory skutečně použité k nasazení.
   :param deadline: Termín inspekce předaný příkazu Docker CLI.
   :return: Neprázdná množina názvů služeb.
   :raises ValueError: Při chybějící nebo nerozpoznatelné sekci služeb.

.. py:function:: inspect_json(kind, names, deadline)

   Ověří úplnost strukturované inspekce konkrétních objektů.

   :param kind: Typ objektu Docker.
   :param names: Jednoznačně vybrané názvy nebo ID.
   :param deadline: Termín inspekce předaný příkazu Docker CLI.
   :return: Seznam inspektovaných objektů.
   :raises ValueError: Pokud inspekce nevrátí právě jeden objekt pro každý název.

.. py:function:: readiness(stack, services, deadline)

   Zkontroluje aktivní úlohy a zdraví pouze požadovaných služeb.

   :param stack: Přesný název cílového stacku.
   :param services: Požadované služby z Compose konfigurace.
   :param deadline: Termín inspekce předaný každému příkazu Docker CLI.
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
