PID verificators
================

Modul verificators.

Funkce
------

.. py:function:: verify_doi(doi)

   Ověří existenci DOI identifikátoru dotazem na API doi.org.

   **Parametry:**

   - ``doi``: Řetězec s DOI identifikátorem, který má být ověřen.

   **Návratová hodnota:**

   Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


.. py:function:: verify_orcid(orcid)

   Ověří existenci ORCID identifikátoru dotazem na veřejné ORCID API.

   **Parametry:**

   - ``orcid``: Řetězec s ORCID identifikátorem, který má být ověřen.

   **Návratová hodnota:**

   Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


.. py:function:: verify_ror(ror)

   Ověří existenci ROR identifikátoru organizace dotazem na ROR API.

   **Parametry:**

   - ``ror``: Řetězec s ROR identifikátorem, který má být ověřen.

   **Návratová hodnota:**

   Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


.. py:function:: verify_wikidata(wikidata)

   Ověří existenci položky Wikidata dotazem na stránku daného záznamu.

   **Parametry:**

   - ``wikidata``: Řetězec s identifikátorem nebo URL záznamu Wikidata, který má být ověřen.

   **Návratová hodnota:**

   Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

