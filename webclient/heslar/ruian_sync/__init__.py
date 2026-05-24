"""
Balíček pro synchronizaci heslářů RÚIAN (kraj/okres/katastr) se zdrojem ČÚZK.

Architektura:

* **Plný (initial) sync** – :class:`shp_importer.ShpUzszSource` čte SHP
  polygony (``1.zip`` 241 MB) a definiční body z VFR ``ST_UZSZ.xml.zip``
  (4.5 MB). Volá se z management commandu ``aktualizuj_ruian_shp``.
* **Denní inkrementální sync** – :class:`provider.FileVfrSource` čte
  denní změnový VFR (``ST_ZKSH``) přes :mod:`vfr_parser` a stahuje ho
  přes :mod:`vfr_download`. Volá se z Celery cronu
  :func:`cron.tasks.sync_ruian_changes`.

Společný syncer (:func:`syncer.sync_full` resp. :func:`syncer.sync_delta`)
přijímá od obou zdrojů :class:`RuianFullState` resp. iterátor
:class:`RuianChangeEvent` a aplikuje upserty + delete na DB.

Veřejné API:

* :class:`provider.RuianSource` – abstrakce zdroje;
* :class:`provider.RuianKrajDTO`, :class:`provider.RuianOkresDTO`,
  :class:`provider.RuianKatastrDTO` – DTO pro přenos hodnot;
* :class:`provider.RuianChangeEvent` – událost upsert/delete pro inkrementální sync;
* :class:`provider.FileVfrSource` – zdroj denního změnového VFR (cron);
* :class:`shp_importer.ShpUzszSource` – kombinovaný zdroj SHP + UZSZ pro plný sync.
"""

from heslar.ruian_sync.provider import (  # noqa: F401
    FileVfrSource,
    RuianChangeEvent,
    RuianKatastrDTO,
    RuianKrajDTO,
    RuianOkresDTO,
    RuianSource,
)
from heslar.ruian_sync.shp_importer import ShpUzszSource  # noqa: F401
