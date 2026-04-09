Skript test_check_container_image_reference_parity.py
=====================================================

Automaticky generovaná dokumentace skriptu ``scripts/test_check_container_image_reference_parity.py``.

Funkce
------

.. py:function:: _compose()

   Popis není k dispozici.

.. py:function:: test_cross_fix_reports_missing_prod_literal_when_not_whitelisted()

   Ověří chybu pro literální repo bez produkčního literálu i whitelistu.

.. py:function:: test_cross_fix_allows_whitelisted_dev_only_repo()

   Potvrdí, že explicitně whitelisted dev-only repo nevrací chybu.

.. py:function:: test_cross_fix_updates_mismatched_repo_present_in_prod()

   Při fix režimu přepíše pin na produkční referenci, pokud repo existuje v prod.

.. py:function:: test_cross_fix_skips_non_literal_images_without_error()

   Neliterální image musí zůstat mimo cross-file porovnání bez falešné chyby.

.. py:function:: test_cross_fix_deduplicates_missing_prod_repo_errors()

   Stejné chybějící repo v jednom consumer compose má být nahlášeno jen jednou.

.. py:function:: test_cross_fix_uses_dockerfile_source_for_repo_alignment()

   Repo může být srovnáno podle lokálního Dockerfile zdroje pravdy.

.. py:function:: test_cross_fix_reports_dockerfile_source_drift()

   Drift vůči Dockerfile source of truth musí vrátit chybu.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_check_container_image_reference_parity.py
   :language: python
   :linenos:
