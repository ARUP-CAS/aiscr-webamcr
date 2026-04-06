PID verificators
================

Modul verificators.

Funkce
------

.. py:function:: verify_doi(doi)

   Ověří existenci DOI identifikátoru dotazem na API doi.org.

   :param doi: Řetězec s DOI identifikátorem, který má být ověřen.

       :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

.. py:function:: verify_orcid(orcid)

   Ověří existenci ORCID identifikátoru dotazem na veřejné ORCID API.

   :param orcid: Řetězec s ORCID identifikátorem, který má být ověřen.

       :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

.. py:function:: verify_ror(ror)

   Ověří existenci ROR identifikátoru organizace dotazem na ROR API.

   :param ror: Řetězec s ROR identifikátorem, který má být ověřen.

       :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

.. py:function:: verify_wikidata(wikidata)

   Ověří existenci položky Wikidata dotazem na stránku daného záznamu.

   :param wikidata: Řetězec s identifikátorem nebo URL záznamu Wikidata, který má být ověřen.

       :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
