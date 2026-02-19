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
   * - Django
     - 5.2.11
     - BSD-3-Clause
     - https://www.djangoproject.com/
   * - Jinja2
     - 3.1.6
     - BSD License
     - https://github.com/pallets/jinja/
   * - MarkupSafe
     - 3.0.3
     - BSD-3-Clause
     - https://github.com/pallets/markupsafe/
   * - PyRTF3
     - 0.47.5
     - GNU General Public License (GPL)
     - https://github.com/xoviat/pyrtf
   * - PySocks
     - 1.7.1
     - BSD
     - https://github.com/Anorov/PySocks
   * - PyYAML
     - 6.0.3
     - MIT License
     - https://pyyaml.org/
   * - Pygments
     - 2.19.2
     - BSD License
     - https://pygments.org
   * - SPARQLWrapper
     - 2.0.0
     - W3C License
     - http://rdflib.github.io/sparqlwrapper
   * - Sphinx
     - 9.1.0
     - BSD-2-Clause
     - https://www.sphinx-doc.org/
   * - Werkzeug
     - 3.1.5
     - BSD-3-Clause
     - https://github.com/pallets/werkzeug/
   * - alabaster
     - 1.0.0
     - BSD License
     - https://alabaster.readthedocs.io/
   * - amqp
     - 5.3.1
     - BSD License
     - http://github.com/celery/py-amqp
   * - asgiref
     - 3.11.1
     - BSD License
     - https://github.com/django/asgiref/
   * - async-generator
     - 1.10
     - Apache Software License; MIT License
     - https://github.com/python-trio/async_generator
   * - attrs
     - 25.4.0
     - MIT
     - https://www.attrs.org/en/stable/changelog.html
   * - babel
     - 2.18.0
     - BSD License
     - https://babel.pocoo.org/
   * - backports.zstd
     - 1.3.0
     - PSF-2.0
     - https://github.com/rogdham/backports.zstd
   * - beautifulsoup4
     - 4.14.3
     - MIT License
     - https://www.crummy.com/software/BeautifulSoup/bs4/
   * - billiard
     - 4.2.4
     - BSD License
     - https://github.com/celery/billiard
   * - brotli
     - 1.2.0
     - MIT
     - https://github.com/google/brotli
   * - celery
     - 5.6.2
     - BSD-3-Clause
     - https://docs.celeryq.dev/
   * - certifi
     - 2026.1.4
     - Mozilla Public License 2.0 (MPL 2.0)
     - https://github.com/certifi/python-certifi
   * - cffi
     - 2.0.0
     - MIT
     - https://cffi.readthedocs.io/en/latest/whatsnew.html
   * - cfgv
     - 3.5.0
     - MIT
     - https://github.com/asottile/cfgv
   * - charset-normalizer
     - 3.4.4
     - MIT
     - https://github.com/jawah/charset_normalizer/blob/master/CHANGELOG.md
   * - click
     - 8.3.1
     - BSD-3-Clause
     - https://github.com/pallets/click/
   * - click-didyoumean
     - 0.3.1
     - MIT License
     - https://github.com/click-contrib/click-didyoumean
   * - click-plugins
     - 1.1.1.2
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
     - 7.13.4
     - Apache-2.0
     - https://github.com/coveragepy/coveragepy
   * - crispy-bootstrap4
     - 2025.6
     - MIT License
     - https://github.com/django-crispy-forms/crispy-bootstrap4
   * - cron_descriptor
     - 2.0.6
     - MIT
     - https://github.com/Salamek/cron-descriptor
   * - cryptography
     - 46.0.5
     - Apache-2.0 OR BSD-3-Clause
     - https://github.com/pyca/cryptography
   * - defusedxml
     - 0.7.1
     - Python Software Foundation License
     - https://github.com/tiran/defusedxml
   * - distlib
     - 0.4.0
     - Python Software Foundation License
     - https://github.com/pypa/distlib
   * - django-add-default-value
     - 0.10.0
     - Apache Software License
     - https://github.com/3YOURMIND/django-add-default-value
   * - django-appconf
     - 1.2.0
     - BSD License
     - https://django-appconf.readthedocs.io/
   * - django-auto-logout
     - 0.5.1
     - BSD License
     - https://github.com/bugov/django-auto-logout
   * - django-autocomplete-light
     - 3.12.1
     - MIT License
     - http://django-autocomplete-light.rtfd.org
   * - django-cacheops
     - 7.2
     - BSD License
     - http://github.com/Suor/django-cacheops
   * - django-celery-beat
     - 2.8.1
     - BSD License
     - https://github.com/celery/django-celery-beat
   * - django-crispy-forms
     - 2.5
     - MIT
     - https://github.com/django-crispy-forms/django-crispy-forms
   * - django-debug-toolbar
     - 6.2.0
     - BSD License
     - https://github.com/django-commons/django-debug-toolbar
   * - django-debug-toolbar-template-profiler
     - 2.1.0
     - BSD License
     - https://github.com/node13h/django-debug-toolbar-template-profiler
   * - django-extensions
     - 4.1
     - MIT
     - https://github.com/django-extensions/django-extensions
   * - django-filter
     - 25.2
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
     - 5.0.0
     - BSD License
     - https://github.com/jazzband/django-model-utils
   * - django-object-actions
     - 5.0.0
     - Apache Software License
     - https://github.com/crccheck/django-object-actions
   * - django-prometheus
     - 2.4.1
     - Apache Software License
     - http://github.com/korfuri/django-prometheus
   * - django-recaptcha
     - 4.1.0
     - BSD License
     - https://github.com/django-recaptcha/django-recaptcha
   * - django-registration
     - 5.2.1
     - BSD License
     - UNKNOWN
   * - django-rosetta
     - 0.10.3
     - MIT License
     - https://github.com/mbi/django-rosetta
   * - django-tables2
     - 2.8.0
     - BSD License
     - https://github.com/jieter/django-tables2/
   * - django-tables2-column-shifter
     - 2.2.0
     - BSD License
     - https://github.com/djk2/django-tables2-column-shifter
   * - django-timezone-field
     - 7.2.1
     - BSD License
     - https://github.com/mfogel/django-timezone-field/
   * - django-widget-tweaks
     - 1.5.1
     - MIT License
     - https://github.com/jazzband/django-widget-tweaks
   * - django_celery_results
     - 2.6.0
     - BSD License
     - https://github.com/celery/django-celery-results
   * - django_compressor
     - 4.6.0
     - MIT
     - https://django-compressor.readthedocs.io/en/latest/
   * - djangorestframework
     - 3.16.1
     - BSD License
     - https://www.django-rest-framework.org/
   * - djangorestframework-xml
     - 2.0.0
     - BSD License
     - https://github.com/jpadilla/django-rest-framework-xml
   * - docutils
     - 0.22.4
     - BSD License; GNU General Public License (GPL); Public Domain
     - https://docutils.sourceforge.io
   * - et_xmlfile
     - 2.0.0
     - MIT License
     - https://foss.heptapod.net/openpyxl/et_xmlfile
   * - filelock
     - 3.24.3
     - MIT
     - https://github.com/tox-dev/py-filelock
   * - freezegun
     - 1.5.5
     - Apache-2.0
     - https://github.com/spulec/freezegun
   * - funcy
     - 2.0
     - BSD License
     - http://github.com/Suor/funcy
   * - h11
     - 0.16.0
     - MIT License
     - https://github.com/python-hyper/h11
   * - identify
     - 2.6.16
     - MIT
     - https://github.com/pre-commit/identify
   * - idna
     - 3.11
     - BSD-3-Clause
     - https://github.com/kjd/idna
   * - imagesize
     - 1.4.1
     - MIT License
     - https://github.com/shibukawa/imagesize_py
   * - importlib_metadata
     - 8.7.1
     - Apache-2.0
     - https://github.com/python/importlib_metadata
   * - inflate64
     - 1.0.4
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://inflate64.readthedocs.io/
   * - kombu
     - 5.6.2
     - BSD-3-Clause
     - https://kombu.readthedocs.io
   * - libsass
     - 0.23.0
     - MIT License
     - https://sass.github.io/libsass-python/
   * - lxml
     - 6.0.2
     - BSD-3-Clause
     - https://lxml.de/
   * - multivolumefile
     - 0.2.3
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://github.com/miurahr/multivolume
   * - mypy_extensions
     - 1.1.0
     - MIT
     - https://github.com/python/mypy_extensions
   * - nodeenv
     - 1.10.0
     - BSD License
     - https://github.com/ekalinin/nodeenv
   * - numpy
     - 2.4.2
     - BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0
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
     - 26.0
     - Apache-2.0 OR BSD-2-Clause
     - https://github.com/pypa/packaging
   * - pandas
     - 3.0.0
     - BSD License
     - https://pandas.pydata.org
   * - pdf2image
     - 1.17.0
     - MIT License
     - https://github.com/Belval/pdf2image
   * - phonenumbers
     - 9.0.24
     - Apache-2.0
     - https://github.com/daviddrysdale/python-phonenumbers
   * - piexif
     - 1.1.3
     - MIT License
     - https://github.com/hMatoba/Piexif
   * - pillow
     - 12.1.1
     - MIT-CMU
     - https://python-pillow.github.io
   * - pip
     - 26.0.1
     - MIT
     - https://pip.pypa.io/
   * - pip-licenses
     - 5.5.1
     - MIT
     - https://github.com/raimon49/pip-licenses
   * - platformdirs
     - 4.9.2
     - MIT
     - https://github.com/tox-dev/platformdirs
   * - polib
     - 1.2.0
     - MIT License
     - https://github.com/izimobil/polib/
   * - pre_commit
     - 4.5.1
     - MIT
     - https://github.com/pre-commit/pre-commit
   * - prettytable
     - 3.17.0
     - BSD-3-Clause
     - https://github.com/prettytable/prettytable
   * - prometheus_client
     - 0.24.1
     - Apache-2.0 AND BSD-2-Clause
     - https://github.com/prometheus/client_python
   * - prompt_toolkit
     - 3.0.52
     - BSD License
     - https://github.com/prompt-toolkit/python-prompt-toolkit
   * - psutil
     - 7.2.2
     - BSD-3-Clause
     - https://github.com/giampaolo/psutil
   * - psycopg2-binary
     - 2.9.11
     - GNU Library or Lesser General Public License (LGPL)
     - https://psycopg.org/
   * - py7zr
     - 1.1.2
     - LGPL-2.1-or-later
     - https://py7zr.readthedocs.io/
   * - pyOpenSSL
     - 25.3.0
     - Apache Software License
     - https://pyopenssl.org/
   * - pybcj
     - 1.0.7
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://pypi.org/project/pybcj
   * - pycparser
     - 3.0
     - BSD-3-Clause
     - https://github.com/eliben/pycparser
   * - pycryptodomex
     - 3.23.0
     - BSD License; Public Domain
     - https://www.pycryptodome.org
   * - pyparsing
     - 3.3.2
     - MIT
     - https://github.com/pyparsing/pyparsing/
   * - pypdf
     - 6.7.0
     - BSD-3-Clause
     - https://github.com/py-pdf/pypdf
   * - pyppmd
     - 1.3.1
     - LGPL-2.1-or-later
     - https://pyppmd.readthedocs.io/
   * - python-crontab
     - 3.3.0
     - LGPLv3
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
     - 2025.2
     - MIT License
     - http://pythonhosted.org/pytz
   * - rarfile
     - 4.2
     - ISC License (ISCL)
     - https://github.com/markokr/rarfile
   * - rcssmin
     - 1.2.2
     - Apache License, Version 2.0
     - https://opensource.perlig.de/rcssmin/
   * - rdflib
     - 7.6.0
     - BSD License
     - https://github.com/RDFLib/rdflib
   * - redis
     - 7.2.0
     - MIT
     - https://github.com/redis/redis-py
   * - reportlab
     - 4.4.10
     - BSD License
     - https://www.reportlab.com/
   * - requests
     - 2.32.5
     - Apache Software License
     - https://requests.readthedocs.io
   * - rjsmin
     - 1.2.5
     - Apache License, Version 2.0
     - https://opensource.perlig.de/rjsmin/
   * - roman-numerals
     - 4.1.0
     - 0BSD OR CC0-1.0
     - https://github.com/AA-Turner/roman-numerals/blob/master/CHANGES.rst
   * - selenium
     - 4.40.0
     - Apache-2.0
     - https://www.selenium.dev
   * - setuptools
     - 82.0.0
     - MIT
     - https://github.com/pypa/setuptools
   * - simplejson
     - 3.20.2
     - Academic Free License (AFL); MIT License
     - https://github.com/simplejson/simplejson
   * - six
     - 1.17.0
     - MIT License
     - https://github.com/benjaminp/six
   * - sniffio
     - 1.3.1
     - Apache Software License; MIT License
     - https://github.com/python-trio/sniffio
   * - snowballstemmer
     - 3.0.1
     - BSD License
     - https://github.com/snowballstem/snowball
   * - sortedcontainers
     - 2.4.0
     - Apache Software License
     - http://www.grantjenks.com/docs/sortedcontainers/
   * - soupsieve
     - 2.8.3
     - MIT
     - https://github.com/facelessuser/soupsieve
   * - sphinx_rtd_theme
     - 3.1.0
     - MIT License
     - https://github.com/readthedocs/sphinx_rtd_theme
   * - sphinxcontrib-applehelp
     - 2.0.0
     - BSD License
     - https://www.sphinx-doc.org/
   * - sphinxcontrib-devhelp
     - 2.0.0
     - BSD License
     - https://www.sphinx-doc.org/
   * - sphinxcontrib-googleanalytics
     - 0.5
     - BSD-3-Clause
     - https://github.com/sphinx-contrib/googleanalytics
   * - sphinxcontrib-htmlhelp
     - 2.1.0
     - BSD License
     - https://www.sphinx-doc.org/
   * - sphinxcontrib-jquery
     - 4.1
     - BSD License
     - https://github.com/sphinx-contrib/jquery/
   * - sphinxcontrib-jsmath
     - 1.0.1
     - BSD License
     - http://sphinx-doc.org/
   * - sphinxcontrib-mermaid
     - 2.0.0
     - BSD License
     - https://github.com/mgaitan/sphinxcontrib-mermaid
   * - sphinxcontrib-qthelp
     - 2.0.0
     - BSD License
     - https://www.sphinx-doc.org/
   * - sphinxcontrib-serializinghtml
     - 2.0.0
     - BSD License
     - https://www.sphinx-doc.org/
   * - sqlparse
     - 0.5.5
     - BSD License
     - https://github.com/andialbrecht/sqlparse
   * - tablib
     - 3.9.0
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
     - 6.5.4
     - Apache Software License
     - http://www.tornadoweb.org/
   * - trio
     - 0.33.0
     - MIT OR Apache-2.0
     - https://github.com/python-trio/trio
   * - trio-typing
     - 0.10.0
     - Apache Software License; MIT License
     - https://github.com/python-trio/trio-typing
   * - trio-websocket
     - 0.12.2
     - MIT License
     - https://github.com/python-trio/trio-websocket
   * - types-certifi
     - 2021.10.8.3
     - Apache Software License
     - https://github.com/python/typeshed
   * - types-urllib3
     - 1.26.25.14
     - Apache Software License
     - https://github.com/python/typeshed
   * - typing_extensions
     - 4.15.0
     - PSF-2.0
     - https://github.com/python/typing_extensions
   * - tzdata
     - 2025.3
     - Apache-2.0
     - https://github.com/python/tzdata
   * - tzlocal
     - 5.3.1
     - MIT License
     - https://github.com/regebro/tzlocal/blob/master/CHANGES.txt
   * - uWSGI
     - 2.0.31
     - GNU General Public License v2 or later (GPLv2+)
     - https://uwsgi-docs.readthedocs.io/en/latest/
   * - urllib3
     - 2.6.3
     - MIT
     - https://github.com/urllib3/urllib3/blob/main/CHANGES.rst
   * - vine
     - 5.1.0
     - BSD License
     - https://github.com/celery/vine
   * - virtualenv
     - 20.36.1
     - MIT
     - https://github.com/pypa/virtualenv
   * - wcwidth
     - 0.6.0
     - MIT
     - https://github.com/jquast/wcwidth
   * - websocket-client
     - 1.9.0
     - Apache Software License
     - https://github.com/websocket-client/websocket-client.git
   * - wrapt
     - 2.1.1
     - Copyright (c) 2013-2025, Graham Dumpleton
     - https://github.com/GrahamDumpleton/wrapt
   * - wsproto
     - 1.3.2
     - MIT
     - https://github.com/python-hyper/wsproto/
   * - xlrd
     - 2.0.2
     - BSD License
     - http://www.python-excel.org/
   * - xlwt
     - 1.3.0
     - BSD License
     - http://www.python-excel.org/
   * - zipp
     - 3.23.0
     - MIT
     - https://github.com/jaraco/zipp


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
     - 1.13.18
     - MIT License
     - https://developer.snapappointments.com/bootstrap-select/
   * - Bootstrap Datepicker
     - 1.10.0
     - Apache License
     - https://bootstrap-datepicker.readthedocs.io/en/latest/
   * - Date Range Picker
     - 3.1
     - MIT License
     - http://www.daterangepicker.com/
   * - Django Autocomplete Light
     -
     - MIT License
     - https://github.com/yourlabs/django-autocomplete-light
   * - Dropzone
     - 5.7.0
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
     - 3.7.1
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
   * - Moment.js
     - 2.30.1
     - MIT License
     - https://momentjs.com
   * - Select2
     - 4.0.13
     - MIT License
     - https://github.com/select2/select2/tree/master
   * - Spin
     - 1.2.5
     - MIT License
     - https://github.com/fgnass/spin.js
   * - html-to-rtf-browser
     - 1.6.1
     - MIT License
     - https://github.com/antoniolucasnobar/html-to-rtf-browser; https://github.com/geraphl/javascript-html-to-rtf-browser


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
     - 0.10.14
     - MIT license
     - https://github.com/danihodovic/celery-exporter
   * - Elasticsearch
     - 8.19.0
     - SSPL, Elastic License 2.0, Apache License 2.0
     - https://github.com/elastic/elasticsearch
   * - Kibana
     - 8.19.0
     - SSPL, Elastic License 2.0, Apache License 2.0
     - https://github.com/elastic/kibana
   * - Logstash
     - 8.19.0
     - SSPL, Elastic License 2.0, Apache License 2.0
     - https://github.com/elastic/logstash
   * - rsync
     - 3.0
     - 
     - https://github.com/eea/eea.docker.rsync
   * - Cadvisor
     - 0.55.1
     - Apache License 2
     - https://github.com/google/cadvisor
   * - Fedora
     - 6.5.1
     - Apache-2.0 License
     - https://github.com/fcrepo/fcrepo
   * - gdal
     - 3.12.1
     - MIT License
     - https://github.com/OSGeo/gdal/pkgs/container/gdal  
   * - Grafana
     - 12.3.1
     - AGPL-3.0 License
     - https://github.com/grafana/grafana
   * - NGINX
     - 1.27.3-alpine3.20
     - BSD 2 License
     - https://github.com/nginxinc/docker-nginx
   * - PostGIS
     - 16-3.4
     - MIT License
     - https://github.com/postgis/docker-postgis
   * - Prometheus
     - 3.8.1
     - Apache-2.0 License
     - https://github.com/prometheus/prometheus
   * - PostgreSQL Server Exporter
     - 0.18.1
     - Apache-2.0 License
     - https://github.com/prometheus-community/postgres_exporter
   * - Redis
     - 8.4.0
     - RSALv2, SSPLv1
     - https://github.com/redis/redis
   * - Prometheus Valkey & Redis Metrics Exporter
     - 1.80.1-alpine
     - MIT license
     - https://github.com/oliver006/redis_exporter
   * - Selenium Grid Standalone with Chromium
     - 143.0
     - Apache License 2.0
     - https://github.com/SeleniumHQ/docker-selenium


