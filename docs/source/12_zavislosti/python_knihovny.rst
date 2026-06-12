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
     - 5.2.15
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
     - 2.20.0
     - BSD-2-Clause
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
     - 3.1.8
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
   * - anyio
     - 4.13.0
     - MIT
     - https://anyio.readthedocs.io/en/stable/versionhistory.html
   * - asgiref
     - 3.11.1
     - BSD License
     - https://github.com/django/asgiref/
   * - attrs
     - 26.1.0
     - MIT
     - https://www.attrs.org/en/stable/changelog.html
   * - babel
     - 2.18.0
     - BSD License
     - https://babel.pocoo.org/
   * - backports.zstd
     - 1.5.0
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
     - 5.6.3
     - BSD-3-Clause
     - https://docs.celeryq.dev/
   * - certifi
     - 2026.5.20
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
     - 3.4.7
     - MIT
     - https://github.com/jawah/charset_normalizer/blob/master/CHANGELOG.md
   * - click
     - 8.4.1
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
     - 7.14.1
     - Apache-2.0
     - https://github.com/coveragepy/coveragepy
   * - crispy-bootstrap5
     - 2026.3
     - MIT
     - https://github.com/django-crispy-forms/crispy-bootstrap5
   * - cron-descriptor
     - 1.4.5
     - MIT License
     - https://github.com/Salamek/cron-descriptor
   * - cryptography
     - 48.0.1
     - Apache-2.0 OR BSD-3-Clause
     - https://github.com/pyca/cryptography
   * - defusedxml
     - 0.7.1
     - Python Software Foundation License
     - https://github.com/tiran/defusedxml
   * - distlib
     - 0.4.2
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
     - 2.9.0
     - BSD License
     - https://github.com/celery/django-celery-beat
   * - django-crispy-forms
     - 2.6
     - MIT
     - https://github.com/django-crispy-forms/django-crispy-forms
   * - django-debug-toolbar
     - 6.3.0
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
     - 5.1.2
     - Apache Software License
     - https://github.com/crccheck/django-object-actions
   * - django-prometheus
     - 2.5.0
     - Apache Software License
     - http://github.com/korfuri/django-prometheus
   * - django-recaptcha
     - 4.1.0
     - BSD License
     - https://github.com/django-recaptcha/django-recaptcha
   * - django-registration
     - 5.2.1
     - BSD License
     - https://django-registration.readthedocs.io/
   * - django-rosetta
     - 0.10.3
     - MIT License
     - https://github.com/mbi/django-rosetta
   * - django-tables2
     - 3.0.0
     - BSD License
     - https://github.com/jieter/django-tables2/
   * - django-tables2-column-shifter
     - 2.2.0
     - BSD License
     - https://github.com/djk2/django-tables2-column-shifter
   * - django-timezone-field
     - 7.2.2
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
     - 3.17.1
     - BSD-3-Clause
     - https://www.django-rest-framework.org
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
     - 3.29.3
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
   * - httpcore
     - 1.0.9
     - BSD-3-Clause
     - https://www.encode.io/httpcore/
   * - httpx
     - 0.28.1
     - BSD License
     - https://github.com/encode/httpx
   * - identify
     - 2.6.19
     - MIT
     - https://github.com/pre-commit/identify
   * - idna
     - 3.18
     - BSD-3-Clause
     - https://github.com/kjd/idna
   * - imagesize
     - 2.0.0
     - MIT License
     - https://github.com/shibukawa/imagesize_py
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
     - 6.1.1
     - BSD-3-Clause
     - https://lxml.de/
   * - multivolumefile
     - 0.2.3
     - GNU Lesser General Public License v2 or later (LGPLv2+)
     - https://github.com/miurahr/multivolume
   * - nodeenv
     - 1.10.0
     - BSD License
     - https://github.com/ekalinin/nodeenv
   * - numpy
     - 2.4.6
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
     - 26.2
     - Apache-2.0 OR BSD-2-Clause
     - https://github.com/pypa/packaging
   * - pandas
     - 3.0.3
     - BSD License
     - https://pandas.pydata.org
   * - pdf2image
     - 1.17.0
     - MIT License
     - https://github.com/Belval/pdf2image
   * - phonenumbers
     - 9.0.32
     - Apache-2.0
     - https://github.com/daviddrysdale/python-phonenumbers
   * - piexif
     - 1.1.3
     - MIT License
     - https://github.com/hMatoba/Piexif
   * - pillow
     - 12.2.0
     - MIT-CMU
     - https://python-pillow.github.io
   * - pip
     - 26.1.2
     - MIT
     - https://pip.pypa.io/
   * - pip-licenses
     - 5.5.5
     - MIT
     - https://github.com/raimon49/pip-licenses
   * - platformdirs
     - 4.10.0
     - MIT
     - https://github.com/tox-dev/platformdirs
   * - polib
     - 1.2.0
     - MIT License
     - https://github.com/izimobil/polib/
   * - pre_commit
     - 4.6.0
     - MIT
     - https://github.com/pre-commit/pre-commit
   * - prettytable
     - 3.17.0
     - BSD-3-Clause
     - https://github.com/prettytable/prettytable
   * - prometheus_client
     - 0.25.0
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
     - 2.9.12
     - GNU Library or Lesser General Public License (LGPL)
     - https://psycopg.org/
   * - py7zr
     - 1.1.2
     - LGPL-2.1-or-later
     - https://py7zr.readthedocs.io/
   * - pyOpenSSL
     - 26.2.0
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
     - 6.13.2
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
   * - python-discovery
     - 1.4.2
     - MIT License
     - https://github.com/tox-dev/python-discovery
   * - python-logstash
     - 0.4.8
     - MIT License
     - https://github.com/vklochan/python-logstash
   * - python-magic
     - 0.4.27
     - MIT License
     - http://github.com/ahupp/python-magic
   * - pytz
     - 2026.2
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
     - 7.4.0
     - MIT
     - https://github.com/redis/redis-py
   * - reportlab
     - 4.5.1
     - BSD License
     - https://www.reportlab.com/
   * - requests
     - 2.34.2
     - Apache Software License
     - https://github.com/psf/requests
   * - rjsmin
     - 1.2.5
     - Apache License, Version 2.0
     - https://opensource.perlig.de/rjsmin/
   * - roman-numerals
     - 4.1.0
     - 0BSD OR CC0-1.0
     - https://github.com/AA-Turner/roman-numerals/blob/master/CHANGES.rst
   * - selenium
     - 4.44.0
     - Apache-2.0
     - https://www.selenium.dev
   * - setuptools
     - 82.0.1
     - MIT
     - https://github.com/pypa/setuptools
   * - simplejson
     - 4.1.1
     - MIT OR AFL-2.1
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
     - 3.1.1
     - BSD-3-Clause
     - https://github.com/snowballstem/snowball
   * - sortedcontainers
     - 2.4.0
     - Apache Software License
     - http://www.grantjenks.com/docs/sortedcontainers/
   * - soupsieve
     - 2.8.4
     - MIT
     - https://github.com/facelessuser/soupsieve
   * - sphinx_rtd_theme
     - 3.1.0
     - MIT License
     - https://sphinx-rtd-theme.readthedocs.io/
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
     - 2.0.2
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
     - 0.10.0
     - MIT
     - https://github.com/astanin/python-tabulate
   * - texttable
     - 1.7.0
     - MIT License
     - https://github.com/foutaise/texttable/
   * - tornado
     - 6.5.7
     - Apache Software License
     - http://www.tornadoweb.org/
   * - trio
     - 0.33.0
     - MIT OR Apache-2.0
     - https://github.com/python-trio/trio
   * - trio-websocket
     - 0.12.2
     - MIT License
     - https://github.com/python-trio/trio-websocket
   * - typing_extensions
     - 4.15.0
     - PSF-2.0
     - https://github.com/python/typing_extensions
   * - tzdata
     - 2026.2
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
     - 2.7.0
     - MIT
     - https://github.com/urllib3/urllib3/blob/main/CHANGES.rst
   * - vine
     - 5.1.0
     - BSD License
     - https://github.com/celery/vine
   * - virtualenv
     - 21.4.3
     - MIT
     - https://github.com/pypa/virtualenv
   * - wcwidth
     - 0.8.1
     - MIT
     - https://github.com/jquast/wcwidth
   * - websocket-client
     - 1.9.0
     - Apache Software License
     - https://github.com/websocket-client/websocket-client.git
   * - wrapt
     - 2.2.1
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


Ostatní knihovny a závislosti
-------------------------------

Použité JavaScript knihovny a Docker image jsou uvedeny v samostatné části dokumentace.

:doc:`Docker image <12_zavislosti/docker_images>`.
:doc:`JavaScript knihovny <12_zavislosti/javascript_knihovny>`.

