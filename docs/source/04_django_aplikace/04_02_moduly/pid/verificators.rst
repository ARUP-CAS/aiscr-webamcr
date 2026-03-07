PID verificators
================

Modul verificators.

Funkce
------

.. py:function:: verify_doi(doi)

   Provádí operaci verify doi.

   :param doi: Textová hodnota `doi` používaná pro vyhledání, pojmenování nebo hlášení stavu.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

.. py:function:: verify_orcid(orcid)

   Provádí operaci verify orcid.

   :param orcid: Parametr ``orcid`` se předává do volání ``get()``.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

.. py:function:: verify_ror(ror)

   Provádí operaci verify ror.

   :param ror: Textová hodnota `ror` používaná pro vyhledání, pojmenování nebo hlášení stavu.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

.. py:function:: verify_wikidata(wikidata)

   Provádí operaci verify wikidata.

   :param wikidata: Kolekce ``wikidata`` zpracovávaná touto funkcí.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
