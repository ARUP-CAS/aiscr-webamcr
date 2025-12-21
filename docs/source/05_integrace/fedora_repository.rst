Fedora repository
=================

**Fedora Repository** je open-source systém pro správu digitálních objektů určený primárně pro knihovny,
archivy, muzea a další instituce, které potřebují dlouhodobě uchovávat a zpřístupňovat digitální obsah.
Architektura Fedora Repository je založena na modulárním přístupu, kde každý digitální objekt je
reprezentován jako kombinace metadat, datových streamů (datastreams) a vztahů k jiným objektům.
Systém využívá persistentní identifikátory (PID) pro jednoznačnou identifikaci objektů a podporuje
různé metadata standardy včetně Dublin Core, MODS či PREMIS. Fedora poskytuje REST API, které
umožňuje programový přístup k objektům a jejich manipulaci, což zajišťuje flexibilní integraci s
externími systémy a aplikacemi.

Z technického hlediska Fedora Repository implementuje principy OAIS (Open Archival Information
System) modelu a zajišťuje dlouhodobou preservaci digitálního obsahu pomocí verzování objektů a
auditních záznamů všech změn. Systém podporuje různé úložné mechanismy pro datové streamy (souborový
systém, databáze, Amazon S3) a umožňuje definovat politiky přístupu pomocí XACML (eXtensible Access
Control Markup Language). Každý objekt může obsahovat libovolný počet datastreams různých typů
(například původní soubor, deriváty pro náhled, OCR text) a systém automaticky spravuje jejich
vztahy a závislosti. Fedora také poskytuje mechanismy pro indexování obsahu pomocí Apache Solr nebo
Elasticsearch, což umožňuje efektivní vyhledávání napříč repozitářem.

Modely s metadaty v Fedoře
---------------------------

Následující modely dědí od třídy ``ModelWithMetadata`` a jejich metadata jsou ukládána do
Fedora Repository:

* ``Adb`` - Archeologická databáze
* ``ArcheologickyZaznam`` - Archeologický záznam
* ``Dokument`` - Dokument
* ``ExterniZdroj`` - Externí zdroj
* ``Heslar`` - Heslář
* ``Let`` - Let
* ``Organizace`` - Organizace
* ``Osoba`` - Osoba
* ``Pian`` - PIAN
* ``Projekt`` - Projekt
* ``RuianKatastr`` - RUIAN katastr
* ``RuianKraj`` - RUIAN kraj
* ``RuianOkres`` - RUIAN okres
* ``SamostatnyNalez`` - Samostatný nález
* ``User`` - Uživatel

