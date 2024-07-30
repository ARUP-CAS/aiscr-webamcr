Použité knihovny a licence
==========================

Knihovny jsou do aplikace instalovány s využitím systému `pip` a jako statické soubory s využitím tagu `<script>`.

Níže je přehled licencí, které knihovny v aplikaci používají.

**MIT Licence** je velmi liberální licence, která umožňuje širokou škálu použití. Umožňuje uživatelům používat, kopírovat,
upravovat, spojovat, publikovat, distribuovat, sublicencovat a/nebo prodávat kopie softwaru a dovoluje uživatelům
držet u sebe zdrojový kód, pokud v souborech softwaru zachovají původní oznámení o autorských právech a licenci.

**GNU General Public License (GPL)** je *copyleft licence*, která vyžaduje, aby modifikované verze open source
software byly distribuovány pod stejnou licencí. To znamená, že každý software, který je odvozen od kódu pod GPL,
musí být také uvolněn pod GPL, pokud je distribuován. GPL zajišťuje, že software a jeho odvozené práce zůstanou
volně dostupné a chrání autorská práva autorů.

**BSD Licence** je sada *permissive* licencí, které jsou méně restriktivní než GPL. Povolují distribuci zdrojového
i binárního kódu s málo omezeními, což znamená, že software může být použit, modifikován a distribuován pro soukromé
i komerční účely. BSD licence obvykle vyžadují pouze zachování oznámení o autorských právech a seznamů podmínek
v redistribuovaných kódech.

**Apache Software License** je *permissive* licence podobná MIT a BSD licencím, ale obsahuje klauzuli o ochraně
proti zneužití jména. To znamená, že uživatelé mohou kopírovat, modifikovat a distribuovat software,
ale nesmí používat jméno projektu nebo jeho přispěvatelů k propagaci odvozených produktů bez předchozího písemného
souhlasu. Licence také explicitně deklaruje, že software je poskytován "tak, jak je", což chrání vývojáře
před právními nároky.

**Mozilla Public License 2.0** je *copyleft* licence, která umožňuje kombinaci MPL kódu s ne-MPL kódem v jednom
projektu. Na rozdíl od GPL, MPL nevyžaduje, aby celý software byl distribuován pod MPL, pokud používá MPL kód.
To umožňuje větší flexibilitu při integraci do různých projektů. Licence chrání vývojáře a zajišťuje, že kód
zůstane otevřený a přístupný pro komunitu.

Knihovny instalované pomocí pip
-------------------------------

Tabulka obsahuje přehled knihoven použitých v projektu, které byly nainstalovány prostřednictvím systému `pip`,
a jejich příslušné licence. Každý řádek v souboru představuje jednu knihovnu a obsahuje následující informace:

1. **Název knihovny**: Toto pole obsahuje oficiální název knihovny nebo softwarového balíčku použitého v projektu.
2. **Verze**: Verze knihovny, která je v projektu použita. Verze je důležitá pro určení kompatibility a zabezpečení knihovny.
3. **Licence**: Typ licence, pod kterou je knihovna distribuována. Licence může určovat, jak může být knihovna použita, modifikována a distribuována. Některé běžné typy licencí zahrnují MIT, GPL, Apache License atd.
4. **Odkaz**: Odkaz na domovskou stránku knihovny

Tento soubor je důležitý pro porozumění právním aspektům použitých knihoven a pro zajištění, že projekt dodržuje licenční požadavky všech použitých závislostí. Je důležité pravidelně aktualizovat tento soubor, aby odrážel jakékoli změny v použitých knihovnách nebo jejich licencích.

.. list-table:: Knihovny instalované s využitím `pip`
   :widths: 25 25 25 25
   :header-rows: 1

   * - Název knihovny
     - Verze
     - Licence
     - Odkaz
   * - Brotli
     - 1.1.0
     - MIT License
     - https://github.com/google/brotli
   * - Django
     - 5.0.7
     - BSD License
     - https://www.djangoproject.com/
   * - PyRTF3
     - 0.47.5
     - GNU General Public License (GPL)
     - https://github.com/xoviat/pyrtf
   * - PySocks
     - 1.7.1
     - BSD
     - https://github.com/Anorov/PySocks
   * - PyYAML
     - 6.0.1
     - MIT License
     - https://pyyaml.org/
   * - amqp
     - 5.2.0
     - BSD License
     - http://github.com/celery/py-amqp
   * - asgiref
     - 3.8.1
     - BSD License
     - https://github.com/django/asgiref/
   * - attrs
     - 23.2.0
     - MIT License
     - https://www.attrs.org/en/stable/changelog.html
   * - beautifulsoup4
     - 4.12.3
     - MIT License
     - https://www.crummy.com/software/BeautifulSoup/bs4/
   * - billiard
     - 4.2.0
     - BSD License
     - https://github.com/celery/billiard
   * - black
     - 24.4.2
     - MIT License
     - https://github.com/psf/black
   * - celery
     - 5.4.0
     - BSD License
     - https://docs.celeryq.dev/
   * - certifi
     - 2024.7.4
     - Mozilla Public License 2.0 (MPL 2.0)
     - https://github.com/certifi/python-certifi
   * - cfgv
     - 3.4.0
     - MIT License
     - https://github.com/asottile/cfgv
   * - chardet
     - 5.2.0
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://github.com/chardet/chardet
   * - charset-normalizer
     - 3.3.2
     - MIT License
     - https://github.com/Ousret/charset_normalizer
   * - click
     - 8.1.7
     - BSD License
     - https://palletsprojects.com/p/click/
   * - click-didyoumean
     - 0.3.1
     - MIT License
     - https://github.com/click-contrib/click-didyoumean
   * - click-plugins
     - 1.1.1
     - BSD License
     - https://github.com/click-contrib/click-plugins
   * - click-repl
     - 0.3.0
     - MIT
     - https://github.com/untitaker/click-repl
   * - confusable-homoglyphs
     - 3.3.1
     - MIT License
     - https://github.com/vhf/confusable_homoglyphs
   * - coverage
     - 7.6.0
     - Apache Software License
     - https://github.com/nedbat/coveragepy
   * - crispy-bootstrap4
     - 2024.1
     - MIT License
     - https://github.com/django-crispy-forms/crispy-bootstrap4
   * - cron-descriptor
     - 1.4.3
     - MIT License
     - https://github.com/Salamek/cron-descriptor
   * - defusedxml
     - 0.7.1
     - Python Software Foundation License
     - https://github.com/tiran/defusedxml
   * - distlib
     - 0.3.8
     - Python Software Foundation License
     - https://github.com/pypa/distlib
   * - django-add-default-value
     - 0.10.0
     - Apache Software License
     - https://github.com/3YOURMIND/django-add-default-value
   * - django-appconf
     - 1.0.6
     - BSD License
     - https://django-appconf.readthedocs.io/
   * - django-auto-logout
     - 0.5.1
     - BSD License
     - https://github.com/bugov/django-auto-logout
   * - django-autocomplete-light
     - 3.11.0
     - MIT License
     - http://django-autocomplete-light.rtfd.org
   * - django-cacheops
     - 7.0.2
     - BSD License
     - http://github.com/Suor/django-cacheops
   * - django-celery-beat
     - 2.6.0
     - BSD License
     - https://github.com/celery/django-celery-beat
   * - django-celery-results
     - 2.5.1
     - BSD License
     - https://github.com/celery/django-celery-results
   * - django-compressor
     - 4.5.1
     - MIT License
     - https://django-compressor.readthedocs.io/en/latest/
   * - django-crispy-forms
     - 2.3
     - MIT License
     - https://github.com/django-crispy-forms/django-crispy-forms
   * - django-debug-toolbar
     - 4.4.6
     - BSD License
     - https://github.com/jazzband/django-debug-toolbar
   * - django-debug-toolbar-template-profiler
     - 2.1.0
     - BSD License
     - https://github.com/node13h/django-debug-toolbar-template-profiler
   * - django-extensions
     - 3.2.3
     - MIT License
     - https://github.com/django-extensions/django-extensions
   * - django-filter
     - 24.2
     - BSD License
     - https://github.com/carltongibson/django-filter/tree/main
   * - django-libsass
     - 0.9
     - BSD License
     - https://github.com/torchbox/django-libsass
   * - django-livereload-server
     - 0.5.1
     - BSD License
     - https://github.com/tjwalch/django-livereload-server
   * - django-model-utils
     - 4.5.1
     - BSD License
     - https://github.com/jazzband/django-model-utils
   * - django-object-actions
     - 4.2.0
     - Apache Software License
     - https://github.com/crccheck/django-object-actions
   * - django-prometheus
     - 2.3.1
     - Apache Software License
     - http://github.com/korfuri/django-prometheus
   * - django-recaptcha
     - 4.0.0
     - BSD License
     - https://github.com/torchbox/django-recaptcha
   * - django-registration
     - 3.3
     - BSD License
     - https://github.com/ubernostrum/django-registration/
   * - django-rosetta
     - 0.10.0
     - MIT License
     - https://github.com/mbi/django-rosetta
   * - django-tables2
     - 2.6.0
     - BSD License
     - https://github.com/jieter/django-tables2/
   * - django-tables2-column-shifter
     - 2.2.0
     - BSD License
     - https://github.com/djk2/django-tables2-column-shifter
   * - django-timezone-field
     - 7.0
     - BSD License
     - https://github.com/mfogel/django-timezone-field/
   * - django-widget-tweaks
     - 1.5.0
     - MIT License
     - https://github.com/jazzband/django-widget-tweaks
   * - djangorestframework
     - 3.15.2
     - BSD License
     - https://www.django-rest-framework.org/
   * - djangorestframework-xml
     - 2.0.0
     - BSD License
     - https://github.com/jpadilla/django-rest-framework-xml
   * - et-xmlfile
     - 1.1.0
     - MIT License
     - https://foss.heptapod.net/openpyxl/et_xmlfile
   * - filelock
     - 3.15.4
     - The Unlicense (Unlicense)
     - https://github.com/tox-dev/py-filelock
   * - funcy
     - 2.0
     - BSD License
     - http://github.com/Suor/funcy
   * - h11
     - 0.14.0
     - MIT License
     - https://github.com/python-hyper/h11
   * - identify
     - 2.6.0
     - MIT License
     - https://github.com/pre-commit/identify
   * - idna
     - 3.7
     - BSD License
     - https://github.com/kjd/idna
   * - inflate64
     - 1.0.0
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - UNKNOWN
   * - isort
     - 5.13.2
     - MIT License
     - https://pycqa.github.io/isort/
   * - kombu
     - 5.3.7
     - BSD License
     - https://kombu.readthedocs.io
   * - libsass
     - 0.23.0
     - MIT License
     - https://sass.github.io/libsass-python/
   * - lxml
     - 5.2.2
     - BSD License
     - https://lxml.de/
   * - multivolumefile
     - 0.2.3
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://github.com/miurahr/multivolume
   * - mypy-extensions
     - 1.0.0
     - MIT License
     - https://github.com/python/mypy_extensions
   * - nodeenv
     - 1.9.1
     - BSD License
     - https://github.com/ekalinin/nodeenv
   * - numpy
     - 2.0.1
     - BSD License
     - https://numpy.org
   * - odfpy
     - 1.4.1
     - Apache Software License; GNU General Public License (GPL); GNU Library or Lesser General Public License (LGPL)
     - https://github.com/eea/odfpy
   * - openpyxl
     - 3.1.5
     - MIT License
     - https://openpyxl.readthedocs.io
   * - outcome
     - 1.3.0.post0
     - Apache Software License; MIT License
     - https://github.com/python-trio/outcome
   * - packaging
     - 24.1
     - Apache Software License; BSD License
     - https://github.com/pypa/packaging
   * - pandas
     - 2.2.2
     - BSD License
     - https://pandas.pydata.org
   * - pathspec
     - 0.12.1
     - Mozilla Public License 2.0 (MPL 2.0)
     - UNKNOWN
   * - pdf2image
     - 1.17.0
     - MIT License
     - https://github.com/Belval/pdf2image
   * - phonenumbers
     - 8.13.40
     - Apache Software License
     - https://github.com/daviddrysdale/python-phonenumbers
   * - pillow
     - 10.4.0
     - Historical Permission Notice and Disclaimer (HPND)
     - https://python-pillow.org
   * - platformdirs
     - 4.2.2
     - MIT License
     - https://github.com/platformdirs/platformdirs
   * - polib
     - 1.2.0
     - MIT License
     - https://github.com/izimobil/polib/
   * - pre-commit
     - 3.8.0
     - MIT License
     - https://github.com/pre-commit/pre-commit
   * - prometheus_client
     - 0.20.0
     - Apache Software License
     - https://github.com/prometheus/client_python
   * - prompt_toolkit
     - 3.0.47
     - BSD License
     - https://github.com/prompt-toolkit/python-prompt-toolkit
   * - psutil
     - 6.0.0
     - BSD License
     - https://github.com/giampaolo/psutil
   * - psycopg2
     - 2.9.9
     - GNU Library or Lesser General Public License (LGPL)
     - https://psycopg.org/
   * - psycopg2-binary
     - 2.9.9
     - GNU Library or Lesser General Public License (LGPL)
     - https://psycopg.org/
   * - py7zr
     - 0.21.0
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://py7zr.readthedocs.io/
   * - pybcj
     - 1.0.2
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://codeberg.org/miurahr/pybcj
   * - pycryptodomex
     - 3.20.0
     - Apache Software License; BSD License; Public Domain
     - https://www.pycryptodome.org
   * - pyparsing
     - 3.1.2
     - MIT License
     - https://github.com/pyparsing/pyparsing/
   * - pypdf
     - 4.3.1
     - BSD License
     - https://github.com/py-pdf/pypdf
   * - pyppmd
     - 1.1.0
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://pyppmd.readthedocs.io/
   * - python-crontab
     - 3.2.0
     - GNU Lesser General Public License v3 or later (LGPLv3+)
     - https://gitlab.com/doctormo/python-crontab/
   * - python-dateutil
     - 2.9.0.post0
     - Apache Software License; BSD License
     - https://github.com/dateutil/dateutil
   * - python-logstash
     - 0.4.8
     - MIT License
     - https://github.com/vklochan/python-logstash
   * - python-magic
     - 0.4.27
     - MIT License
     - http://github.com/ahupp/python-magic
   * - pytz
     - 2024.1
     - MIT License
     - http://pythonhosted.org/pytz
   * - pyzstd
     - 0.16.0
     - BSD License
     - https://github.com/Rogdham/pyzstd
   * - rarfile
     - 4.2
     - ISC License (ISCL)
     - https://github.com/markokr/rarfile
   * - rcssmin
     - 1.1.2
     - Apache License, Version 2.0
     - http://opensource.perlig.de/rcssmin/
   * - redis
     - 5.0.7
     - MIT License
     - https://github.com/redis/redis-py
   * - reportlab
     - 4.2.2
     - BSD License
     - https://www.reportlab.com/
   * - requests
     - 2.32.3
     - Apache Software License
     - https://requests.readthedocs.io
   * - rjsmin
     - 1.2.2
     - Apache License, Version 2.0
     - http://opensource.perlig.de/rjsmin/
   * - selenium
     - 4.23.1
     - Apache Software License
     - https://www.selenium.dev
   * - simplejson
     - 3.19.2
     - Academic Free License (AFL); MIT License
     - https://github.com/simplejson/simplejson
   * - six
     - 1.16.0
     - MIT License
     - https://github.com/benjaminp/six
   * - sniffio
     - 1.3.1
     - Apache Software License; MIT License
     - https://github.com/python-trio/sniffio
   * - sortedcontainers
     - 2.4.0
     - Apache Software License
     - http://www.grantjenks.com/docs/sortedcontainers/
   * - soupsieve
     - 2.5
     - MIT License
     - https://github.com/facelessuser/soupsieve
   * - sqlparse
     - 0.5.1
     - BSD License
     - https://github.com/andialbrecht/sqlparse
   * - tablib
     - 3.6.1
     - MIT License
     - https://tablib.readthedocs.io
   * - tabulate
     - 0.9.0
     - MIT License
     - https://github.com/astanin/python-tabulate
   * - texttable
     - 1.7.0
     - MIT License
     - https://github.com/foutaise/texttable/
   * - tornado
     - 6.4.1
     - Apache Software License
     - http://www.tornadoweb.org/
   * - trio
     - 0.26.0
     - Apache Software License; MIT License
     - https://github.com/python-trio/trio
   * - trio-websocket
     - 0.11.1
     - MIT License
     - https://github.com/python-trio/trio-websocket
   * - typing_extensions
     - 4.12.2
     - Python Software Foundation License
     - https://github.com/python/typing_extensions
   * - tzdata
     - 2024.1
     - Apache Software License
     - https://github.com/python/tzdata
   * - uWSGI
     - 2.0.26
     - GNU General Public License v2 or later (GPLv2+)
     - https://uwsgi-docs.readthedocs.io/en/latest/
   * - urllib3
     - 2.2.2
     - MIT License
     - https://github.com/urllib3/urllib3/blob/main/CHANGES.rst
   * - vine
     - 5.1.0
     - BSD License
     - https://github.com/celery/vine
   * - virtualenv
     - 20.26.3
     - MIT License
     - https://github.com/pypa/virtualenv
   * - websocket-client
     - 1.8.0
     - Apache Software License
     - https://github.com/websocket-client/websocket-client.git
   * - wrapt
     - 1.16.0
     - BSD License
     - https://github.com/GrahamDumpleton/wrapt
   * - wsproto
     - 1.2.0
     - MIT License
     - https://github.com/python-hyper/wsproto/
   * - xlrd
     - 2.0.1
     - BSD License
     - http://www.python-excel.org/
   * - xlwt
     - 1.3.0
     - BSD License
     - http://www.python-excel.org/


Knihovny vkládané jako statické soubory
---------------------------------------

.. list-table:: Knihovny v jazyce Javascript
   :widths: 25 25 25 25
   :header-rows: 1

   * - Název knihovny
     - Verze
     - Licence
     - Odkaz
   * - Bootstrap
     - 4.5.3
     - MIT License
     - https://getbootstrap.com/
   * - Bootstrap Icons
     - 1.5.0
     - MIT License
     - https://icons.getbootstrap.com/
   * - Bootstrap Select
     - 1.13.14
     - MIT License
     - https://developer.snapappointments.com/bootstrap-select/
   * - Bootstrap Datepicker
     - 1.9.0
     - Apache License
     - https://bootstrap-datepicker.readthedocs.io/en/latest/
   * - Django Autocomplete Light
     -
     - MIT License
     - https://github.com/yourlabs/django-autocomplete-light
   * - Dropzone
     -
     - MIT License
     - https://www.dropzone.dev/
   * - Easytimer
     -
     - MIT License
     - https://albert-gonzalez.github.io/easytimer.js/
   * - Google Tag Manager
     -
     -
     - https://tagmanager.google.com/#/home
   * - Heatmap.js
     - 2.0.5
     - MIT License
     - https://www.patrick-wied.at/static/heatmapjs/
   * - jQuery
     - 3.5.1
     - MIT License
     - https://jquery.com/
   * - Leaflet
     - 1.9.4
     - BSD License
     - https://leafletjs.com/
   * - Leaflet Context Menu
     - 1.5.1
     - MIT License
     - https://github.com/aratcliffe/Leaflet.contextmenu
   * - Leaflet Control Search
     -
     - MIT License
     - https://github.com/stefanocudini/leaflet-search
   * - Leaflet Coordinates
     -
     - Creative Commons Attribution 3.0 Unported License.
     - https://github.com/MrMufflon/Leaflet.Coordinates/tree/master
   * - Leaflet Draw
     - 1.0.4
     - MIT License
     - https://github.com/Leaflet/Leaflet.draw
   * - Leaflet Easy Button
     - v1
     - MIT License
     - https://danielmontague.com/projects/easyButton.js/v1/examples/
   * - Leaflet FeatureGroup SubGroup
     -
     - BSD License
     - https://github.com/ghybs/Leaflet.FeatureGroup.SubGroup/tree/master
   * - Leaflet Fullscreen
     - 1.0.1
     - ISC License
     - https://github.com/Leaflet/Leaflet.fullscreen
   * - Leaflet Heatmap Overlay
     -
     - MIT License
     - https://www.patrick-wied.at/static/heatmapjs/plugin-leaflet-layer.html
   * - Leaflet Marker Cluster
     - 1.5.3
     - MIT License
     - https://github.com/Leaflet/Leaflet.markercluster
   * - Leaflet Measure
     -
     - MIT License
     - https://github.com/ljagis/leaflet-measure
   * - Leaflet Spin
     - 1.1.2
     - MIT License
     - https://github.com/makinacorpus/Leaflet.Spin
   * - Leaflet TileLayer Grayscale
     -
     - WTFPL license
     - https://github.com/Zverik/leaflet-grayscale
   * - Leaflet Messagebox
     - 1.1
     - BSD License
     - https://github.com/tinuzz/leaflet-messagebox
   * - LercDecode
     - 1.0.1
     - Apache Software License
     - https://unpkg.com/browse/lerc@1.0.1/
   * - Select2
     - 4.0.13
     - MIT License
     - https://github.com/select2/select2/tree/master
   * - Spin
     - 1.2.5
     - MIT License
     - https://github.com/fgnass/spin.js


Docker image
---------------------------------------

.. list-table:: Image použité pro provoz
   :widths: 25 25 25 25
   :header-rows: 1

   * - Název image
     - Verze
     - Licence
     - Odkaz
   * - celery-exporter
     - 0.10.8
     - MIT license
     - https://github.com/danihodovic/celery-exporter
   * - Elasticsearch
     - 8.14.1
     - SSPL, Elastic License 2.0, Apache License 2.0
     - https://github.com/elastic/elasticsearch
   * - Kibana
     - 8.14.1
     - SSPL, Elastic License 2.0, Apache License 2.0
     - https://github.com/elastic/kibana
   * - Logstash
     - 8.14.1
     - SSPL, Elastic License 2.0, Apache License 2.0
     - https://github.com/elastic/logstash
   * - eeacms/rsync:2.4
     - 2.4
     - 
     - https://github.com/eea/eea.docker.rsync
   * - Cadvisor
     - 0.49.1
     - Apache License 2
     - https://github.com/google/cadvisor
   * - Fedora
     - 6.4.0
     - Apache-2.0 License
     - https://github.com/fcrepo/fcrepo
   * - ghcr.io/osgeo/gdal:ubuntu-small
     - 3.9.1
     - MIT License
     - https://github.com/OSGeo/gdal/pkgs/container/gdal  
   * - Grafana
     - 10.2.8
     - AGPL-3.0 License
     - https://github.com/grafana/grafana
   * - docker-nginx
     - 1.26.1
     - BSD 2 License
     - https://github.com/nginxinc/docker-nginx
   * - postgis/postgis
     - 14-3.3
     - MIT License
     - https://github.com/postgis/docker-postgis
   * - Prometheus
     - 2.45.6
     - Apache-2.0 License
     - https://github.com/prometheus/prometheus
   * - Postgres-exporter
     - 0.15.0
     - Apache-2.0 License
     - https://github.com/prometheus-community/postgres_exporter
   * - Redis
     - 7.2.5
     - RSALv2, SSPLv1
     - https://github.com/redis/redis
   * - Redis exporter
     - 1.61.0
     - MIT license
     - https://github.com/oliver006/redis_exporter
   * - selenium/standalone-firefox
     - 127.0
     - Apache License 2.0
     - https://github.com/SeleniumHQ/docker-selenium


