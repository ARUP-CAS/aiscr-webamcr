PID formuláře
=============

Definice formulářů.

Třídy
------

.. py:class:: FormWithOrcid

   Implementuje komponentu ``FormWithOrcid`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean_orcid()

      Doplní k zadanému ORCID identifikátoru prefix URL ``https://orcid.org/`` a vrátí jej, nebo ``None`` pro prázdný vstup.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.



.. py:class:: FormWithWikidata

   Implementuje komponentu ``FormWithWikidata`` v rámci aplikace.

   **Metody:**

   .. py:method:: clean_wikidata()

      Doplní k zadanému identifikátoru Wikidata prefix URL ``https://www.wikidata.org/entity/`` a vrátí jej, nebo ``None`` pro prázdný vstup.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.



.. py:class:: UpdateDocumentObjectIdentifierFileForm

   Implementuje komponentu ``UpdateDocumentObjectIdentifierFileForm`` v rámci aplikace.

