Ukládání souborů
================

Soubory jsou ukládány do repozitáře Fedora.

Podporované soubory podle stránky
----------------------------------

``nahrat-soubor/pas/``
~~~~~~~~~~~~~~~~~~~~~~

* ``image/*``

``nahrat-soubor/dokument/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``application/pdf``

``nahrat-soubor/projekt/``
~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``image/*``
* ``.zip``
* ``.ZIP``
* ``.rar``
* ``.RAR``
* ``.7z``
* ``.7Z``
* ``application/vnd.ms-excel``
* ``application/vnd.openxmlformats-officedocument.wordprocessingml.document``
* ``application/docx``
* ``application/pdf``
* ``text/plain``
* ``application/msword``
* ``application/vnd.openxmlformats-officedocument.spreadsheetml.sheet``
* ``application/vnd.oasis.opendocument.text``
* ``application/vnd.oasis.opendocument.spreadsheet``

Poznámky
--------

1. Pro správnou funkci uploadu a stahování/mazání souborů je klíčový sloupec ``soubor.path`` který obsahuje cestu k souboru.
2. Cesta k souboru je relativní např. ``soubory/2021/07/01/2937995434_archeologie.txt`` v dockeru ukazuje na ``/var/lib/docker/volumes/<container_name>_static_data/_data/media/soubory/2021/07/01/2937995434_archeologie.txt`` v docker hostu.

