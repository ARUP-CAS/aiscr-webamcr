API signály
===========

Definice signálů.

Funkce
------

.. py:function:: validate_pas_request_target_fields(sender, instance)

   Pro PAS-specifické cíle (XML import, evidenční číslo patch, fotografie upload)
   vyžaduje vyplněné ``ident_cely`` i ``samostatny_nalez`` v okamžiku, kdy je
   záznam úspěšně dokončen (``status == success``). Stav ``failure`` validace
   cíleně neaktivuje — k chybě může dojít před tím, než je ``ident_cely``
   vůbec známé (např. chybějící soubor v XML importu, neexistující záznam pro
   PATCH/UPLOAD), a vynucení vyplnění by zablokovalo legitimní zápis chyby.

   :param sender: Třída modelu (``ApiRequestLog``).
   :param instance: Konkrétní ukládaný záznam.
   :param kwargs: Další argumenty signálu (nepoužity).

   :raises ValidationError: Pokud je ``request_target`` PAS-specifický, záznam
       je ve stavu ``success`` a chybí ``ident_cely`` nebo ``samostatny_nalez``.
