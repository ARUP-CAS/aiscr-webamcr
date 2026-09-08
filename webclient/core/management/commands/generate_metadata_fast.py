import concurrent.futures.thread
import functools
import hashlib
import json
import logging
import os
import random
import re
import socket
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from decimal import Decimal
from threading import Lock

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from django.utils.translation import gettext as _
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

_RETRYABLE_EXCEPTIONS = (requests.exceptions.ConnectionError, requests.exceptions.Timeout)

#: Timeout (sekundy) pro běžné HTTP požadavky na Fedoru. Bez timeoutu je
#: ``requests.exceptions.Timeout`` v ``_RETRYABLE_EXCEPTIONS`` nedosažitelný (výchozí
#: chování ``requests`` je čekat neomezeně) a zaseknuté TCP spojení by worker zablokovalo
#: natrvalo, ne jen na dobu jednoho pokusu. Hodnota je záměrně vyšší než ``timeout=10``
#: v ``core/repository_connector.py`` - ta je pro jednu operaci v běžném provozu, kdežto
#: tady Fedora obsluhuje N paralelních workerů najednou a odpovídá výrazně pomaleji.
_HTTP_TIMEOUT = 60

#: Timeout (sekundy) pro commit transakce - řádově vyšší než ``_HTTP_TIMEOUT``, protože
#: commit je zdaleka nejdražší operace: Fedora při něm persistuje celý OCFL objekt
#: (container + metadata + všechny soubory záznamu) a updatuje ``containment`` index pro
#: sdílené rodiče (``/record``, ``/model/{model}/member``). Právě na tom indexu vzniká
#: pod souběhem zámková kontence - měřeno na lokálním běhu (issue #3967): Fedora tam
#: hlásila `deadlock detected` na `UPDATE containment SET updated = ? WHERE fedora_id = ?`.
#: Krátký timeout je tu nebezpečný: vypršení NEZNAMENÁ, že commit selhal, jen že jsme se
#: nedočkali odpovědi - a slepé zopakování záznamu pak vytvoří ve Fedoře duplikát
#: (kolize Slugu se nevyhodnotí jako chyba, Fedora zdroj přejmenuje na náhodné UUID).
_COMMIT_TIMEOUT = 300

#: HTTP status kódy z Fedory, které se považují za přechodné (stojí za retry) - server
#: chyby (5xx, typicky přetížení/konflikt při souběžném zápisu do stejného sdíleného
#: rodiče, např. `/model/{model}/member`), 409 Conflict a 410 Gone (Fedora transakce má
#: timeout - výchozí 3 minuty - a záznam s hodně soubory drží jednu transakci celou
#: dobu jeho zpracování; po expiraci transakce vrátí 410 na každý další request v ní.
#: Rollback v ``_process_record`` proběhne bez efektu - transakce už neexistuje - takže
#: samotné opakování celého záznamu v nové transakci je bezpečné). Cokoli jiného (4xx)
#: je považováno za trvalou chybu naší strany a neopakuje se.
_RETRYABLE_STATUS_CODES = {409, 410, 500, 502, 503, 504}

#: Vytahuje identifikátor člena z ``ldp:contains`` trojice v n-triples odpovědi Fedory
#: (objekt trojice je plné URI, poslední segment je hledaný ident) - viz ``list_model_members``.
_MEMBER_RE = re.compile(r"<[^>]*/member/([^/>]+)>\s*\.?\s*$")

#: Horní strop celkové doby zpracování JEDNOHO záznamu (sekundy), napříč všemi pokusy.
#: Bez něj by šlo ``--max-retries 20`` × (``_COMMIT_TIMEOUT`` 300 s + backoff) až na ~2,2
#: hodiny na jediný záznam - a hlavně by nešlo rozeznat "pomalu to zkouší dál" od
#: "definitivně zaseknuté", takže watchdog níž by neměl smysluplnou hranici.
_RECORD_TIME_BUDGET = 600

#: Po jaké době bez dokončení se úloha považuje za zaseknutou a přestane se na ni čekat.
#: Musí být s rezervou nad ``_RECORD_TIME_BUDGET``, aby se neopouštěly záznamy, které jen
#: legitimně dojíždějí opakování. Vlákno samotné se ukončit nedá (viz ``_run_parallel``).
_STUCK_TIMEOUT = 900

#: Jak často se kontroluje, jestli něco neuvízlo (sekundy).
_WATCHDOG_INTERVAL = 30

#: Velikost HTTP connection poolu na vlákno. Výchozích 10 v urllib3 je méně než běžný
#: počet workerů, takže se spojení nad limit vytvářela a hned zahazovala - a každé nové
#: spojení znamená nový překlad jména (viz ``_run_parallel`` a issue #3967, kde uvíznutí
#: v ``getaddrinfo`` zastavilo celý běh).
_POOL_SIZE = 32

#: Viz stejnojmenná konstanta v ``generate_metadata.py``.
_BATCH_PER_WORKER = 10

#: Pevná cesta k ``placeholder_manifest.json`` - placeholdery jsou součástí této
#: Django aplikace (``core/management/commands/placeholders/``), takže cesta funguje
#: stejně lokálně i v kontejneru bez ohledu na to, kam je repozitář nasazený.
_PLACEHOLDER_MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "placeholders", "placeholder_manifest.json")


@functools.lru_cache(maxsize=1)
def _get_schema_by_name():
    """
    Vrací mapu ``{název třídy modelu -> (třída, fedora model name)}``.

    Odvozeno z ``DocumentGenerator._get_schema_dict()`` (jediný zdroj pravdy pro
    fedora model name daného modelu), místo aby ho tento soubor duplikoval na dvou
    místech (dřívější ``_MODEL_NAME_MAP`` a lokální ``model_map`` v
    ``_handle_metadata``). Mapování musí zůstat v souladu s
    ``FedoraRepositoryConnector._get_model_name`` v ``core/repository_connector.py``
    - ta duplikace je záměrná, viz docstring ``_FastFedoraWriter``. Výsledek se
    cachuje - volá se z ``_process_record`` na každý zpracovaný záznam, sestavovat
    ho pokaždé znovu (i když jde jen o dict comprehension nad už importovanými
    třídami) by na statisících záznamů zbytečně přidávalo režii.

    :return: Mapa název třídy -> ``(třída, fedora_model_name)``.
    """
    from xml_generator.generator import DocumentGenerator

    return {cls.__name__: (cls, name) for cls, name in DocumentGenerator._get_schema_dict().items()}


def _format_duration(seconds):
    """
    Naformátuje počet sekund jako čitelný interval (``"1h 05m"``, ``"3m 12s"``, ``"7s"``).

    :param seconds: Počet sekund.

        :return: Naformátovaný interval.
    """
    seconds = max(0, int(seconds))
    hodiny, zbytek = divmod(seconds, 3600)
    minuty, vteriny = divmod(zbytek, 60)
    if hodiny:
        return f"{hodiny}h {minuty:02d}m"
    if minuty:
        return f"{minuty}m {vteriny:02d}s"
    return f"{vteriny}s"


def _po_davkach(iterable, velikost):
    """
    Rozdělí iterátor na seznamy o nejvýše ``velikost`` položkách.

    Viz stejnojmenná funkce v ``generate_metadata.py`` - duplikováno, aby byl tento
    příkaz samostatný a nezávisel na interních detailech sourozeneckého modulu.

    :param iterable: Vstupní iterátor.
    :param velikost: Maximální počet položek v jedné dávce.

        :return: Generátor seznamů.
    """
    davka = []
    for polozka in iterable:
        davka.append(polozka)
        if len(davka) >= velikost:
            yield davka
            davka = []
    if davka:
        yield davka


class FastFedoraWriteError(Exception):
    """Vyvolá se, když Fedora vrátí na zápis jiný než 2xx status kód."""

    def __init__(self, url, status_code, text):
        """
        Inicializuje výjimku.

        :param url: URL požadavku, který selhal.
        :param status_code: HTTP status kód odpovědi.
        :param text: Tělo chybové odpovědi.
        """
        self.url = url
        self.status_code = status_code
        super().__init__(f"{status_code} {url}: {text[:300]}")


class FedoraSlugCollision(Exception):
    """
    Fedora dostala ``Slug``, který už v cílovém kontejneru existuje.

    Fedora tenhle případ **nehlásí jako chybu** - vrátí 201 a zdroj potichu přejmenuje na
    náhodné UUID (ověřeno proti běžící instanci). Bez explicitní kontroly ``Location`` tak
    opakování záznamu, jehož commit ve skutečnosti prošel, tiše vyrobí duplikát; ten se
    navíc zaloguje jako úspěch. Viz ``_FastFedoraWriter.create_record``.
    """

    def __init__(self, ident_cely, location):
        """
        Inicializuje výjimku.

        :param ident_cely: Identifikátor, který se pokoušel zapsat.
        :param location: Cesta, kterou Fedora zdroji ve skutečnosti přidělila.
        """
        self.ident_cely = ident_cely
        self.location = location
        super().__init__(f"Slug '{ident_cely}' už existuje, Fedora zdroj přejmenovala na '{location}'")


def _is_retryable(exc: Exception) -> bool:
    """
    Rozhodne, zda má smysl výjimku opakovat (přechodná chyba), nebo ne (trvalá chyba
    naší strany - opakování by jen zbytečně bušilo do Fedory se stejným výsledkem).

    :param exc: Zachycená výjimka.

        :return: ``True`` pro síťové chyby a Fedora 5xx/409 (viz ``_RETRYABLE_STATUS_CODES``).
    """
    if isinstance(exc, _RETRYABLE_EXCEPTIONS):
        return True
    if isinstance(exc, FastFedoraWriteError):
        return exc.status_code in _RETRYABLE_STATUS_CODES
    return False


class _FastFedoraWriter:
    """
    Minimalistický zapisovač do Fedory pro hromadné generování obsahu do **prázdné**
    instance (issue #3967).

    Záměrně oddělený od ``core.repository_connector.FedoraRepositoryConnector`` (na
    žádost při review), aby se tyto zkratky nemohly omylem použít v běžném provozním
    toku aplikace. Ve srovnání s ``FedoraRepositoryConnector`` chybí:

    - GET kontrola existence containeru/metadat/binárky před vytvořením (Fedora je
      prázdná, není co kontrolovat),
    - GET kontrola stávajícího creatora před jeho nastavením (``DELETE WHERE`` je
      no-op, pokud creator ještě neexistuje, takže samotný PATCH stačí).

    **Fedora transakce (``Atomic-ID``) se ale používá** - ne kvůli atomicitě, ale kvůli
    místu na disku: bez transakce vytvoří Fedora **novou OCFL verzi na každý HTTP
    request**, a každá verze si nese vlastní ``inventory.json`` + sidecar a přepisuje
    i nesouvisející hlavičky (`.fcrepo/fcr-root.json`). Empiricky ověřeno (issue #3967):
    záznam s 1 souborem (9 mutací - container, metadata, creator patch, file container,
    binary container, orig, creator patch, thumb, creator patch) bez transakce vytvoří
    9 OCFL verzí, s transakcí (všechny mutace se sbalí do jednoho commitu) jen **1**
    verzi - 23 souborů/22,6 KB místo řádově víc. Cena je tomu úměrná: +2 HTTP requesty
    (begin/commit) na dávku mutací, ale při stovkách tisíc záznamů jde o řádový rozdíl
    v místě na disku, ne v rychlosti.

    Mapování ``_MODEL_NAME_MAP`` a RDF šablony musí zůstat v souladu s
    ``FedoraRepositoryConnector`` (``_get_model_name``, ``_get_creator_rdf_data``);
    při jejich změně aktualizuj obě místa.
    """

    def __init__(self, base_url, user_ident):
        """
        Inicializuje zapisovač.

        :param base_url: Základní URL Fedora repozitáře (``.../rest/{FEDORA_SERVER_NAME}``),
            už s IP adresou místo jména - viz ``Command._get_writer``.
        :param user_ident: Identifikátor uživatele zapsaný jako ``dcterms:creator``.
        """
        from django.conf import settings

        self.base_url = base_url
        self.rest_root = base_url.rsplit("/", 1)[0]
        self.user_ident = user_ident
        self.server_name = settings.FEDORA_SERVER_NAME
        self.auth = HTTPBasicAuth(settings.FEDORA_USER, settings.FEDORA_USER_PASSWORD)
        # Commit/rollback transakce vyžaduje admin auth - stejně jako
        # ``FedoraTransaction._send_transaction_request`` v repository_connector.py.
        self.admin_auth = HTTPBasicAuth(settings.FEDORA_ADMIN_USER, settings.FEDORA_ADMIN_USER_PASSWORD)
        self._thread_local = threading.local()

    def _session(self) -> requests.Session:
        """
        Vrací ``requests.Session`` pro aktuální vlákno (jedna na vlákno - opakované
        použití TCP spojení, ``requests.Session`` není bezpečná pro sdílení mezi vlákny).

        Používá se pro požadavky pod běžnou identitou (``FEDORA_USER``) - pro
        commit/rollback transakce (admin identita) viz ``_admin_session``, NIKDY ne
        tahle metoda (jiná identita na stejné session by sdílela cookie jar).

        :return: Session aktuálního vlákna pro běžnou identitu.
        """
        session = getattr(self._thread_local, "session", None)
        if session is None:
            session = requests.Session()
            session.auth = self.auth
            self._nastav_pool(session)
            self._thread_local.session = session
        return session

    def _admin_session(self) -> requests.Session:
        """
        Vrací ``requests.Session`` pro aktuální vlákno, oddělenou od ``_session`` a
        vyhrazenou pro admin identitu (commit/rollback transakce).

        Fedora (Tomcat + Shiro) si po prvním přihlášení uloží subjekt do servletové
        session a vrací cookie ``JSESSIONID``. Kdyby requestům pod ``FEDORA_USER`` i
        ``FEDORA_ADMIN_USER`` sloužila jedna ``requests.Session``, sdílely by i cookie
        jar a Fedora by admin požadavek vyhodnotila pod identitou, která session
        založila jako první - stejný bug, jaký se řešil ve
        ``FedoraRepositoryConnector._get_session``/``_fedora_admin_session`` v
        ``repository_connector.py`` (větev feature/372, commit "Oprava fedora_session":
        sdílená session způsobovala 403 na admin-only operacích). Proto samostatná
        session i tady, přestože obě běží ve stejném vlákně.

        :return: Session aktuálního vlákna pro admin identitu.
        """
        session = getattr(self._thread_local, "admin_session", None)
        if session is None:
            session = requests.Session()
            session.auth = self.admin_auth
            self._nastav_pool(session)
            self._thread_local.admin_session = session
        return session

    @staticmethod
    def _nastav_pool(session):
        """
        Zvětší HTTP connection pool session, ať se spojení opravdu recyklují.

        Výchozí ``pool_maxsize`` v urllib3 je 10; při vyšším počtu workerů se spojení nad
        ten limit zakládala a hned zahazovala, takže se pořád znovu překládalo jméno
        serveru. Právě v tom překladu (``getaddrinfo``) uvízlo vlákno a zastavilo celý
        běh (issue #3967) - méně nových spojení tedy znamená méně příležitostí k uváznutí.

        :param session: ``requests.Session``, které se pool nastavuje.
        """
        adapter = requests.adapters.HTTPAdapter(pool_connections=_POOL_SIZE, pool_maxsize=_POOL_SIZE)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

    def _creator_rdf(self):
        """
        Vrací turtle fragment s ``dcterms:creator`` pro vložení do nově vytvářeného zdroje.

        :return: Turtle RDF řetězec.
        """
        return (
            f"@prefix dcterms: <http://purl.org/dc/terms/> . "
            f"<> dcterms:creator <info:fedora/{self.server_name}/record/{self.user_ident}> ."
        )

    def _creator_sparql_update(self):
        """
        Vrací SPARQL update, který nastaví ``dcterms:creator`` (bez GET kontroly stávající hodnoty).

        :return: SPARQL update řetězec.
        """
        return (
            "PREFIX dcterms: <http://purl.org/dc/terms/>\n"
            "DELETE WHERE { <> dcterms:creator ?oldCreator .};\n"
            f"INSERT DATA {{ <> dcterms:creator <info:fedora/{self.server_name}/record/{self.user_ident}> .}};"
        )

    def _request(self, method, url, headers, data, tx_url=None):
        """
        Odešle HTTP požadavek a ověří, že odpověď je 2xx.

        :param method: ``"post"`` nebo ``"patch"``.
        :param url: Cílová URL.
        :param headers: HTTP hlavičky požadavku.
        :param data: Tělo požadavku.
        :param tx_url: URL aktivní Fedora transakce (viz ``begin_transaction``); pokud
            je zadaná, přidá se hlavička ``Atomic-ID``, aby požadavek patřil do dané
            transakce místo rovnou zápisu (a nové OCFL verze) na místě.

            :raises FastFedoraWriteError: Pokud odpověď není 2xx.
        """
        if tx_url:
            headers = {**headers, "Atomic-ID": tx_url}
        response = getattr(self._session(), method)(
            url, headers=headers, data=data, verify=False, timeout=_HTTP_TIMEOUT
        )
        if not str(response.status_code).startswith("2"):
            raise FastFedoraWriteError(url, response.status_code, response.text)
        return response

    def begin_transaction(self) -> str:
        """
        Založí novou Fedora transakci.

        :return: URL transakce (pro hlavičku ``Atomic-ID`` na dalších požadavcích a
            pro ``commit_transaction``/``rollback_transaction``).

            :raises FastFedoraWriteError: Pokud se transakci nepodaří založit, nebo
                odpověď neobsahuje identifikátor transakce v hlavičce ``Location``.
        """
        url = f"{self.rest_root}/fcr:tx"
        response = self._session().post(url, verify=False, timeout=_HTTP_TIMEOUT)
        if not str(response.status_code).startswith("2"):
            raise FastFedoraWriteError(url, response.status_code, response.text)
        # URL transakce se bere PŘESNĚ tak, jak ji vrátila Fedora, neskládá se z
        # `rest_root`. Fedora si `Atomic-ID` ověřuje proti vlastní podobě URI, takže
        # jakýkoli rozdíl (jiný host, jiný port) skončí na `409 Invalid transaction id`.
        location = response.headers.get("Location", "")
        if not re.search(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", location):
            raise FastFedoraWriteError(url, response.status_code, "Location header neobsahuje ID transakce.")
        return location

    def commit_transaction(self, tx_url: str):
        """
        Potvrdí transakci - všechny mutace provedené s touto ``Atomic-ID`` se sbalí do
        jedné nové OCFL verze na dotčený objekt (viz docstring třídy).

        :param tx_url: URL transakce z ``begin_transaction``.

            :raises FastFedoraWriteError: Pokud commit selže.
        """
        response = self._admin_session().put(tx_url, verify=False, timeout=_COMMIT_TIMEOUT)
        if not str(response.status_code).startswith("2"):
            raise FastFedoraWriteError(tx_url, response.status_code, response.text)

    def rollback_transaction(self, tx_url: str):
        """
        Zruší transakci. Chyba se jen zaloguje, ať nepřekryje původní chybu, kvůli které
        se rollback volá - ale zahodit ji potichu nelze, protože neuzavřená transakce je
        drahá.

        Fedora drží zámek na dotčených záznamech **v paměti** a uvolní ho jen při commitu
        nebo rollbacku; samotné vypršení transakce zámek neuvolní. O vypršelé se stará
        naplánovaná úloha, která ale běží s periodou ``fcrepo.session.timeout`` (v našem
        nasazení 1 hodina). Neúspěšný rollback tedy může zablokovat záznam až na dvě
        hodiny a všechny naše další pokusy o něj skončí na
        ``409 ... is being updated by another transaction`` (reálně se to stalo, issue #3967).
        Proto se kontroluje i návratový kód (dřív se hlídala jen síťová výjimka, takže
        odmítnutý rollback prošel bez povšimnutí) a jednou se to zkusí znovu.

        :param tx_url: URL transakce z ``begin_transaction``.
        """
        duvod = None
        for pokus in (1, 2):
            try:
                response = self._admin_session().delete(tx_url, verify=False, timeout=_HTTP_TIMEOUT)
            except requests.exceptions.RequestException as exc:
                duvod = str(exc)
            else:
                # 404/410 = transakce už neexistuje, tedy není co uvolňovat.
                if str(response.status_code).startswith("2") or response.status_code in (404, 410):
                    return
                duvod = f"{response.status_code}: {response.text[:200]}"
            if pokus == 1:
                time.sleep(1)
        logger.warning(
            "core.management.commands.generate_metadata_fast.rollback_failed",
            extra={"tx_url": tx_url, "error": duvod},
        )

    @staticmethod
    def _zkontroluj_slug(ident_cely, response, ocekavany_suffix):
        """
        Ověří, že Fedora zdroj skutečně založila pod požadovaným ``Slug``.

        Při kolizi Fedora nevrátí chybu, ale 201 s ``Location`` na náhodné UUID - viz
        ``FedoraSlugCollision``. Kontrola hlavičky je jediný spolehlivý způsob, jak
        kolizi rozpoznat; dřívější pokus předvídat ji dotazem "existuje už záznam?" před
        opakováním se neosvědčil, protože po neúspěšném commitu je záznam ve Fedoře
        viditelný až se zpožděním několika sekund (měřeno, issue #3967).

        :param ident_cely: Požadovaný identifikátor.
        :param response: Odpověď na POST, který zdroj zakládal.
        :param ocekavany_suffix: Cesta, na kterou musí ``Location`` končit.

            :raises FedoraSlugCollision: Pokud ``Location`` odpovídá jinému (přejmenovanému) zdroji.
        """
        location = (response.headers.get("Location") or "").rstrip("/")
        if location and not location.endswith(ocekavany_suffix):
            raise FedoraSlugCollision(ident_cely, location)

    def create_record(self, ident_cely, model_name, document: bytes, hash512: str, tx_url=None):
        """
        Vytvoří kompletní záznam (container, model link, metadata) jedním průchodem.

        :param ident_cely: Celý identifikátor záznamu (``Slug`` containeru).
        :param model_name: Fedora model name pro link (``_MODEL_NAME_MAP``).
        :param document: Vygenerovaný XML dokument metadat.
        :param hash512: SHA-512 hash ``document``.
        :param tx_url: URL aktivní Fedora transakce (viz ``begin_transaction``) - všechny
            čtyři requesty se sbalí do jedné OCFL verze při ``commit_transaction``.
        """
        record_url = f"{self.base_url}/record/"
        response = self._request(
            "post",
            record_url,
            {
                "Slug": ident_cely,
                "Link": '<http://fedora.info/definitions/v4/repository#ArchivalGroup>;rel="type"',
                "Content-Type": "text/turtle",
            },
            self._creator_rdf(),
            tx_url=tx_url,
        )
        self._zkontroluj_slug(ident_cely, response, f"/record/{ident_cely}")
        link_url = f"{self.base_url}/model/{model_name}/member"
        response = self._request(
            "post",
            link_url,
            {"Slug": ident_cely, "Content-Type": "text/turtle"},
            "@prefix ore: <http://www.openarchives.org/ore/terms/> . "
            "@prefix dcterms: <http://purl.org/dc/terms/> . "
            f"<> ore:proxyFor <info:fedora/{self.server_name}/record/{ident_cely}> ; "
            f"dcterms:creator <info:fedora/{self.server_name}/record/{self.user_ident}> .",
            tx_url=tx_url,
        )
        self._zkontroluj_slug(ident_cely, response, f"/model/{model_name}/member/{ident_cely}")
        # CREATE_METADATA se posílá na container (ne na `/metadata`) se `Slug: metadata` -
        # stejně jako `FedoraRepositoryConnector.save_metadata`/`_get_request_url`.
        metadata_url = f"{self.base_url}/record/{ident_cely}/metadata"
        self._request(
            "post",
            f"{self.base_url}/record/{ident_cely}",
            {
                "Content-Type": "application/xml",
                "Content-Disposition": 'attachment; filename="metadata.xml"',
                "Digest": f"sha-512={hash512}",
                "Slug": "metadata",
            },
            document,
            tx_url=tx_url,
        )
        self._request(
            "patch",
            f"{metadata_url}/fcr:metadata",
            {"Content-Type": "application/sparql-update"},
            self._creator_sparql_update(),
            tx_url=tx_url,
        )

    def list_model_members(self, model_name):
        """
        Vrátí množinu identifikátorů zapsaných ve Fedoře pod ``/model/{model}/member``.

        Používá se pro závěrečnou kontrolu konzistence (viz ``Command._zkontroluj_konzistenci``).
        Odpověď se čte proudově - u velkých modelů (``pian`` mívá přes 70 tisíc členů) jde
        o řádově megabajty ``ldp:contains`` trojic a není důvod je držet v paměti naráz.

        :param model_name: Fedora model name (viz ``_get_schema_by_name``).

            :return: Množina identifikátorů (poslední segment cesty každého člena).

            :raises FastFedoraWriteError: Pokud dotaz vrátí jiný status kód než 200/404.
        """
        url = f"{self.base_url}/model/{model_name}/member"
        response = self._session().get(
            url,
            headers={"Accept": "application/n-triples"},
            verify=False,
            timeout=_HTTP_TIMEOUT,
            stream=True,
        )
        try:
            if response.status_code == 404:
                return set()
            if response.status_code != 200:
                raise FastFedoraWriteError(url, response.status_code, response.text)
            identy = set()
            response.encoding = response.encoding or "utf-8"
            for radek in response.iter_lines(decode_unicode=True):
                if not radek or "ldp#contains" not in radek:
                    continue
                match = _MEMBER_RE.search(radek)
                if match:
                    identy.add(match.group(1))
            return identy
        finally:
            response.close()

    def is_repository_empty(self):
        """
        Ověří, že ``/record`` kolekce v repozitáři neobsahuje žádný záznam.

        Nahrazuje kontrolu existence jednotlivých containerů (ta by běh výrazně
        zpomalila) jedním rychlým dotazem na začátku běhu - viz docstring ``Command``.

        Odpověď se žádá v ``application/n-triples`` (ne ``text/turtle``) záměrně -
        n-triples serializace nepoužívá prefixy, takže se v textu vždy objeví plné
        ``http://www.w3.org/ns/ldp#contains`` URI. Kontrola na ``"ldp:contains"`` by
        záludně záviselo na tom, že fcrepo zvolí zrovna tenhle turtle prefix.

        Odpověď se čte proudově (``stream=True``) a čtení se ukončí, jakmile se najde
        první výskyt hledaného URI - právě u neprázdného repozitáře (ten, který má tahle
        metoda odhalit) může mít úplný výpis containment trojic desítky MB; není důvod
        stahovat ho celý, když stačí najít jeden triple.

        :return: ``True``, pokud ``/record`` neobsahuje žádný ``ldp:contains`` triple
            (nebo vůbec neexistuje), jinak ``False``.

            :raises FastFedoraWriteError: Pokud dotaz vrátí jiný status kód než 200/404.
        """
        response = self._session().get(
            f"{self.base_url}/record",
            headers={"Accept": "application/n-triples"},
            verify=False,
            timeout=_HTTP_TIMEOUT,
            stream=True,
        )
        try:
            if response.status_code == 404:
                return True
            if response.status_code != 200:
                raise FastFedoraWriteError(f"{self.base_url}/record", response.status_code, response.text)
            marker = b"http://www.w3.org/ns/ldp#contains"
            tail = b""
            for chunk in response.iter_content(chunk_size=65536):
                if marker in tail + chunk:
                    return False
                tail = chunk[-len(marker) :]
            return True
        finally:
            response.close()

    def create_file_container(self, ident_cely, tx_url=None):
        """
        Vytvoří sdílený ``/file`` container záznamu (jednou na záznam, ne na soubor).

        :param ident_cely: Celý identifikátor záznamu.
        :param tx_url: URL aktivní Fedora transakce (viz ``begin_transaction``).
        """
        self._request(
            "post",
            f"{self.base_url}/record/{ident_cely}",
            {"Slug": "file", "Content-Type": "text/turtle"},
            self._creator_rdf(),
            tx_url=tx_url,
        )

    def create_binary_file(
        self,
        ident_cely,
        uuid,
        file_name,
        mimetype,
        orig_bytes,
        orig_sha512,
        thumb_bytes=None,
        thumb_sha512=None,
        thumb_large_bytes=None,
        thumb_large_sha512=None,
        tx_url=None,
    ):
        """
        Vloží placeholder binárku (``orig``) a volitelně náhledy na konkrétní ``uuid``.

        ``uuid`` se pošle jako ``Slug``, takže výsledná cesta v repozitáři odpovídá
        už existujícímu ``soubor.path`` v DB - žádný zápis do DB není potřeba.

        :param ident_cely: Celý identifikátor záznamu, pod který soubor patří.
        :param uuid: UUID souboru z existujícího ``soubor.path`` (`.../file/{uuid}`).
        :param file_name: Název souboru (``Content-Disposition``, přípona pro náhled).
        :param mimetype: Mimetype ``orig`` obsahu.
        :param orig_bytes: Obsah placeholderu pro ``orig``.
        :param orig_sha512: SHA-512 hash ``orig_bytes``.
        :param thumb_bytes: Obsah placeholder náhledu (100x100 PNG), nebo ``None`` pro přeskočení.
        :param thumb_sha512: SHA-512 hash ``thumb_bytes``.
        :param thumb_large_bytes: Obsah placeholder velkého náhledu (800x800 PNG), nebo ``None``.
        :param thumb_large_sha512: SHA-512 hash ``thumb_large_bytes``.
        :param tx_url: URL aktivní Fedora transakce (viz ``begin_transaction``) - ideálně
            sdílená s ostatními soubory téhož záznamu (a s ``create_file_container``),
            aby se celá skupina sbalila do jedné OCFL verze.
        """
        file_url = f"{self.base_url}/record/{ident_cely}/file"
        self._request(
            "post", file_url, {"Content-Type": "text/turtle", "Slug": uuid}, self._creator_rdf(), tx_url=tx_url
        )

        resource_url = f"{file_url}/{uuid}"
        self._request(
            "post",
            resource_url,
            {
                "Content-Type": mimetype,
                "Content-Disposition": f'attachment; filename="{file_name}"'.encode("utf-8"),
                "Digest": f"sha-512={orig_sha512}",
                "Slug": "orig",
            },
            orig_bytes,
            tx_url=tx_url,
        )
        self._request(
            "patch",
            f"{resource_url}/orig/fcr:metadata",
            {"Content-Type": "application/sparql-update"},
            self._creator_sparql_update(),
            tx_url=tx_url,
        )

        thumb_stem = file_name[: file_name.rfind(".")] if "." in file_name else file_name
        for data, sha512, slug in (
            (thumb_bytes, thumb_sha512, "thumb"),
            (thumb_large_bytes, thumb_large_sha512, "thumb-large"),
        ):
            if data is None:
                continue
            self._request(
                "post",
                resource_url,
                {
                    "Content-Type": "image/png",
                    "Content-Disposition": f'attachment; filename="{thumb_stem}.png"'.encode("utf-8"),
                    "Digest": f"sha-512={sha512}",
                    "Slug": slug,
                },
                data,
                tx_url=tx_url,
            )
            self._request(
                "patch",
                f"{resource_url}/{slug}/fcr:metadata",
                {"Content-Type": "application/sparql-update"},
                self._creator_sparql_update(),
                tx_url=tx_url,
            )


def _load_placeholders(manifest_path=_PLACEHOLDER_MANIFEST_PATH):
    """
    Načte ``placeholder_manifest.json`` a předčte obsah všech placeholder + náhled souborů do paměti.

    SHA-512 hash se vždy počítá znovu z přečtených bajtů, do Fedory jde jen tato
    dopočítaná hodnota. Kdyby se poslal `Digest: sha-512=<manifest>` neodpovídající
    tělu požadavku, Fedora by na každý takový soubor vracela 409.

    Neshoda proti manifestu se zaloguje jako WARNING (`placeholder_hash_mismatch`)
    a načtení nespadne. **Není to očekávaný stav** - konce řádků chrání
    `.gitattributes` (`placeholders/** -text`), takže každý checkout dostane bajty
    shodné s blobem. Neshoda tedy znamená buď zastaralý manifest, nebo změněný či
    poškozený placeholder, a je třeba ji prošetřit: v issue #3967 přesně takto vyšlo
    najevo, že `placeholder_01.pdf` a `placeholder_20.txt` mají v manifestu hash
    CRLF-poškozených bajtů (u PDF s rozbitými `xref` offsety), protože manifest byl
    vygenerován na Windows working tree, který git po opravě `.gitattributes` už
    nepřepsal - a `git status` to nehlásil, protože index měl zapsanou konvertovanou
    velikost.

    :param manifest_path: Cesta k ``placeholder_manifest.json`` (výchozí umístění viz
        ``_PLACEHOLDER_MANIFEST_PATH`` - parametr existuje hlavně kvůli testům).

        :return: Mapa ``mimetype -> {"orig_bytes", "orig_sha512", "thumb_bytes", "thumb_sha512",
            "thumb_large_bytes", "thumb_large_sha512"}``.
    """
    base_dir = os.path.dirname(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    def read(rel_path, manifest_sha512):
        with open(os.path.join(base_dir, rel_path), "rb") as f:
            data = f.read()
        computed_sha512 = hashlib.sha512(data).hexdigest()
        if computed_sha512 != manifest_sha512:
            logger.warning(
                "core.management.commands.generate_metadata_fast.placeholder_hash_mismatch",
                extra={"file": rel_path, "manifest_sha512": manifest_sha512, "computed_sha512": computed_sha512},
            )
        return data, computed_sha512

    placeholders = {}
    for mimetype, entry in manifest.items():
        thumb = entry.get("thumb")
        thumb_large = entry.get("thumb_large")
        orig_bytes, orig_sha512 = read(entry["file"], entry["sha512"])
        thumb_bytes = thumb_sha512 = thumb_large_bytes = thumb_large_sha512 = None
        if thumb:
            thumb_bytes, thumb_sha512 = read(thumb["file"], thumb["sha512"])
        if thumb_large:
            thumb_large_bytes, thumb_large_sha512 = read(thumb_large["file"], thumb_large["sha512"])
        placeholders[mimetype] = {
            "orig_bytes": orig_bytes,
            "orig_sha512": orig_sha512,
            "thumb_bytes": thumb_bytes,
            "thumb_sha512": thumb_sha512,
            "thumb_large_bytes": thumb_large_bytes,
            "thumb_large_sha512": thumb_large_sha512,
        }
    return placeholders


class Command(BaseCommand):
    """
    Django management příkaz pro rychlé hromadné generování XML metadat a placeholder
    souborů do **prázdné** Fedory (issue #3967, migrace fedory bez kopírování dat).

    Vychází z ``generate_metadata``, ale místo přes ``ModelWithMetadata.save_metadata``
    (GET kontroly existence, Fedora transakce s begin/commit) zapisuje přímo přes
    ``_FastFedoraWriter`` - viz jeho docstring pro seznam vynechaných kroků. Určeno
    výhradně pro jednorázové naplnění čerstvé, prázdné Fedora instance; při běhu proti
    Fedoře s existujícími záznamy hrozí duplicitní/kolidující zdroje.

    Jeden běh, jedna OCFL verze na záznam: u modelů, které mají přílohy
    (``Projekt``/``Dokument``/``SamostatnyNalez``), se jejich soubory vloží **ve
    stejné Fedora transakci** jako container/link/metadata (viz ``_process_record``).
    Soubory jsou totiž potomci téže ArchivalGroup jako metadata daného záznamu, takže
    by jejich zpracování v jiné transakci vytvořilo na tomtéž OCFL objektu druhou
    verzi navíc - měřením ověřeno (issue #3967), že počet OCFL verzí určuje počet
    **transakcí**, ne počet mutací v nich. Proto žádné dodatečné dogenerování souborů
    zvlášť neexistuje - buď se vygenerují rovnou (výchozí), nebo vůbec (``--bez-souboru``).

    Protože se soubory generují rovnou, placeholdery (``_PLACEHOLDER_MANIFEST_PATH``,
    umístěné v ``core/management/commands/placeholders/`` vedle tohoto souboru) se
    ověří **hned na začátku** ``handle`` - pokud se manifest nedá načíst, celý příkaz
    skončí (``CommandError``) bez jakéhokoli zápisu do Fedory, aby se běh na
    statisících záznamů nezačal a nespadl až v polovině na špatné cestě k manifestu.

    Placeholder nahrazuje skutečný obsah souboru, takže po migraci ``Soubor.sha_512``/
    ``size_mb`` v DB přestanou odpovídat tomu, co je reálně ve Fedoře. Volitelný
    ``--aktualizovat-db`` tohle srovná - po úspěšném zápisu přepíše obě pole na hodnoty
    odpovídající vloženému placeholderu (viz ``_flush_db_updates``, volá se hromadně po
    doběhnutí modelu, ne po každém souboru zvlášť). Bez něj zůstane DB ukazovat
    hash/velikost původního souboru, který ale ve Fedoře není - což může být žádoucí,
    pokud se DB řeší jinak (odsud opt-in, ne výchozí chování).

    Příklady použití::

        python manage.py generate_metadata_fast --workers 20
        python manage.py generate_metadata_fast --model Dokument --workers 20 --aktualizovat-db
        python manage.py generate_metadata_fast --model Heslar --workers 20 --bez-souboru
    """

    help = _("core.management.commands.generate_metadata_fast.Command.help")

    def add_arguments(self, parser):
        """
        Registruje příkazové argumenty.

        :param parser: Argumentový parser pro přidání nových parametrů příkazu.
        """
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help="Název třídy modelu (např. Projekt, Dokument). Pokud není zadán, zpracují se všechny modely.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximální počet zpracovaných záznamů (na model, pokud není zadán --model).",
        )
        parser.add_argument(
            "--start-with-pk",
            type=int,
            default=None,
            help=(
                "Primární klíč, od kterého se má začít zpracování (``pk__gte``). Bez "
                "--model se aplikuje na všech 15 modelů stejně - pro navázání po pádu "
                "proto použij vždy spolu s --model."
            ),
        )
        parser.add_argument("--workers", type=int, default=1, help="Počet paralelních vláken (1 = sekvenční běh).")
        parser.add_argument(
            "--max-retries",
            type=int,
            default=20,
            help="Maximální počet opakování jednoho záznamu při přechodné chybě (viz _is_retryable).",
        )
        parser.add_argument(
            "--bez-souboru",
            action="store_true",
            default=False,
            help=(
                "Negenerovat soubory (Projekt/Dokument/SamostatnyNalez) - jen XML "
                "metadata. Bez tohoto přepínače musí jít načíst placeholder_manifest.json "
                "(viz core/management/commands/placeholders/)."
            ),
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help=(
                "Přeskočí kontrolu, že /record je prázdné. Použij výhradně pro "
                "navázání po pádu spolu s --start-with-pk nastaveným za poslední "
                "úspěšně zpracovaný záznam - jinak hrozí duplicitní zdroje (viz "
                "docstring třídy Command)."
            ),
        )
        parser.add_argument(
            "--jen-kontrola",
            action="store_true",
            default=False,
            help=(
                "Negenerovat nic, jen porovnat DB proti Fedoře a vypsat rozdíly "
                "(chybějící a přebývající záznamy). Hodí se pro prověření už dokončeného běhu."
            ),
        )
        parser.add_argument(
            "--bez-kontroly",
            action="store_true",
            default=False,
            help="Přeskočit závěrečnou kontrolu konzistence DB vs Fedora po dogenerování.",
        )
        parser.add_argument(
            "--aktualizovat-db",
            action="store_true",
            default=False,
            help=(
                "Po úspěšném vložení placeholderu do Fedory přepíše Soubor.sha_512/size_mb "
                "v DB na hodnoty odpovídající vloženému placeholderu (ne původnímu, skutečnému "
                "souboru) - bez toho DB po migraci ukazuje hash/velikost obsahu, který ve "
                "Fedoře reálně není. Se --bez-souboru nemá žádný efekt - tam se soubory "
                "vůbec nezapisují, není co v DB aktualizovat. "
                "Mutuje DB hromadně - použij vědomě, ne jen 'pro jistotu'."
            ),
        )

    # Nastavují se v `_handle_metadata`; výchozí hodnoty tady drží `handle()` funkční
    # i na cestách, kde se generování nespustí (např. `--jen-kontrola`).
    _zaseknute_ulohy = 0
    _pocet_selhani = 0

    @staticmethod
    def _get_writer():
        """
        Vytvoří ``_FastFedoraWriter`` napojený na aktuálně nakonfigurovanou Fedoru.

        :return: Instance ``_FastFedoraWriter``.
        """
        from core.log_middleware import LogMiddleware
        from django.conf import settings

        hostname = settings.FEDORA_SERVER_HOSTNAME
        port = settings.FEDORA_PORT_NUMBER
        # Jméno se přeloží JEDNOU tady a dál se pracuje s IP. Jinak ho překládá znovu
        # každé nově navazované spojení, a protože jich při stovkách tisíc záznamů vzniknou
        # desetitisíce, stačí aby jediný překlad uvízl a přijdeme o worker (reálně se to
        # stalo - vlákno zaseklé v `getaddrinfo`/netlink zastavilo celý běh, issue #3967).
        # `timeout=` v requests na překlad jména nesahá, takže jinak se proti tomu bránit
        # nedá. Hlavička `Host` se záměrně NEpřepisuje na původní jméno: Fedora podle ní
        # generuje URI transakcí, takže by `Atomic-ID` složené z IP neodpovídalo tomu, co
        # Fedora čeká, a každý zápis by skončil na `409 Invalid transaction id`. Uloženým
        # datům to nevadí - v OCFL se drží interní `info:fedora/...` identifikátory,
        # ověřeno grepem přes uložený záznam (žádné absolutní http URI tam není).
        try:
            ip = socket.gethostbyname(hostname)
        except OSError as exc:
            raise CommandError(f"Nepodařilo se přeložit '{hostname}' na IP adresu: {exc}")
        base_url = f"{settings.FEDORA_PROTOCOL}://{ip}:{port}/rest/{settings.FEDORA_SERVER_NAME}"
        return _FastFedoraWriter(base_url, LogMiddleware.get_user_id())

    @staticmethod
    def _flush_db_updates(db_updates, db_updates_lock, placeholders):
        """
        Hromadně přepíše ``Soubor.sha_512``/``size_mb`` na hodnoty odpovídající placeholderu,
        který byl skutečně vložen do Fedory (viz ``--aktualizovat-db`` a "Poznámka k
        záměru" v review issue #3967).

        Migrace vědomě nahrazuje obsah souborů placeholdery - bez tohoto kroku by
        ``Soubor.sha_512``/``size_mb`` v DB dál odpovídaly původnímu (skutečnému)
        souboru, který ale ve Fedoře reálně není. Krok je opt-in (``--aktualizovat-db``),
        protože jde o hromadnou mutaci produkční DB, ne jen zápis do Fedory.

        Všechny soubory se stejným mimetype dostaly bajtově identický placeholder (viz
        ``_load_placeholders``), takže mají i identický ``sha_512``/``size_mb`` - není
        důvod dělat samostatný ``UPDATE`` na každý soubor zvlášť (u run na statisících
        souborů šlo o stejný počet round-tripů, review issue #3967). Místo toho jeden
        ``UPDATE ... WHERE pk IN (...)`` na dávku pro každý mimetype.

        ``size_mb`` se počítá stejně jako ``RepositoryBinaryFile.size_mb`` v
        ``core/repository_connector.py`` (``size / 1024**2``, MiB) - ne ``/1_000_000``,
        ať DB po migraci odpovídá jednotkám, které používá zbytek aplikace.

        :param db_updates: Mapa ``mimetype -> [Soubor.pk, ...]`` nasbíraná v ``_process_record``,
            nebo ``None`` bez ``--aktualizovat-db`` (pak se nic nedělá).
        :param db_updates_lock: Zámek chránící ``db_updates`` (viz ``_process_record``).
        :param placeholders: Mapa mimetype -> placeholder obsah (``_load_placeholders``).
        """
        from core.models import Soubor

        if db_updates is None:
            return
        # Watchdog zaseknutá vlákna jen opouští, nezabíjí je - takové vlákno může do
        # `db_updates` ještě zapsat. Iterovat přímo přes sdílený dict by proto mohlo
        # skončit `RuntimeError: dictionary changed size during iteration`, takže se
        # pod zámkem udělá kopie (review issue #3967).
        with db_updates_lock:
            db_updates = {mimetype: list(pks) for mimetype, pks in db_updates.items()}

        for mimetype, pks in db_updates.items():
            if not pks:
                continue
            entry = placeholders[mimetype]
            size_mb = Decimal(len(entry["orig_bytes"])) / Decimal(1024**2)
            for chunk in _po_davkach(pks, 5000):
                Soubor.objects.filter(pk__in=chunk).update(sha_512=entry["orig_sha512"], size_mb=size_mb)

    @staticmethod
    def _process_record(obj, writer, max_retries, failures, placeholders=None, db_updates=None, db_updates_lock=None):
        """
        Vygeneruje XML metadata pro jeden záznam a vloží je do Fedory rychlou cestou.

        Pokud má záznam vlastní soubory (``Projekt``/``Dokument``/``SamostatnyNalez`` -
        viz ``obj.soubory``) a je předaný ``placeholders`` (načtený manifest, viz
        ``_load_placeholders``), vloží se **ve stejné transakci** jako metadata. Soubory
        jsou totiž potomci téže Fedora ArchivalGroup jako container/metadata daného
        záznamu - kdyby se zpracovaly v jiné transakci, vznikla by na tomtéž OCFL
        objektu druhá verze navíc (viz docstring ``_FastFedoraWriter`` a issue #3967 -
        měření ukázalo, že počet OCFL verzí určuje počet transakcí, ne počet mutací v nich).

        Generování XML dokumentu a načtení seznamu souborů záznamu proběhne **jednou,
        před** retry smyčkou - na rozdíl od samotného zápisu do Fedory nezávisí na
        předchozím (neúspěšném) pokusu, takže by se při retry jen zbytečně opakovalo
        (DB dotazy, XPath nad schématem) beze změny výsledku.

        Selhání (vyčerpané retries, nebo rovnou trvalá chyba - viz ``_is_retryable``)
        nezastaví celý běh - zaloguje se a záznam se přidá do ``failures`` k pozdějšímu
        dohledání/opakování (přes ``--start-with-pk``); u běhu na statisících záznamů
        by jinak jediný problémový záznam shodil celé hodiny běžící generování. Chybějící
        placeholder pro konkrétní mimetype je stejný případ - přeskočí se jen ten soubor
        (zbytek záznamu i metadata se uloží normálně), ale skip se taky zapíše do
        ``failures``, ať jde po běhu dohledat (jinak by o něm věděl jen log).

        :param obj: Instance modelu (``ModelWithMetadata``).
        :param writer: Sdílený ``_FastFedoraWriter``.
        :param max_retries: Maximální počet opakování při přechodných chybách.
        :param failures: Sdílený seznam pro zápis ``(pk, ident_cely, error)`` při selhání.
        :param placeholders: Mapa mimetype -> placeholder obsah (``_load_placeholders``),
            nebo ``None`` při ``--bez-souboru`` - pak se soubory záznamu vůbec neřeší.
        :param db_updates: Sdílený ``defaultdict(list)`` mimetype -> ``[Soubor.pk, ...]``
            (viz ``--aktualizovat-db`` a ``_flush_db_updates``), nebo ``None`` bez
            ``--aktualizovat-db``. Po úspěšném zápisu se sem jen přidá pk - samotný
            ``UPDATE`` proběhne hromadně až po doběhnutí celého modelu.
        :param db_updates_lock: Zámek pro ``db_updates`` (sdílený mezi vlákny), povinný
            pokud je ``db_updates`` zadané.
        """
        from core.models import SouborVazby
        from xml_generator.generator import DocumentGenerator

        if not obj.ident_cely:
            logger.warning(
                "core.management.commands.generate_metadata_fast.missing_ident_cely",
                extra={"pk": obj.pk, "model": obj.__class__.__name__},
            )
            return
        model_name = _get_schema_by_name()[obj.__class__.__name__][1]
        zacatek = time.time()
        try:
            document = DocumentGenerator(obj).generate_document()
            hash512 = hashlib.sha512(document).hexdigest()
            soubory = []
            if placeholders is not None and isinstance(getattr(obj, "soubory", None), SouborVazby):
                soubory = [
                    (s.pk, s.path.rsplit("/", 1)[-1], s.nazev, s.mimetype)
                    for s in obj.soubory.soubory.exclude(path="").exclude(path__isnull=True)
                ]
        except Exception as exc:
            # Chyba při generování dokumentu/čtení seznamu souborů není nikdy
            # retryovatelná (na rozdíl od zápisu do Fedory níže) - jde o data/logiku,
            # ne o přechodný síťový/serverový stav, opakování by dalo stejný výsledek.
            logger.error(
                "core.management.commands.generate_metadata_fast.record_failed",
                extra={"pk": obj.pk, "ident_cely": obj.ident_cely, "error": str(exc)},
            )
            failures.append((obj.pk, obj.ident_cely, str(exc)))
            return

        # Chybějící placeholder je vlastnost dat záznamu, ne pokusu o zápis - vyhodnotí se
        # jednou, ještě před retry smyčkou. Dřív tahle větev byla uvnitř smyčky, takže
        # každé opakování záznamu (vyvolané jiným, retryovatelným souborem) zapsalo tentýž
        # chybějící placeholder do logu i do `failures` znovu (review issue #3967).
        melo_soubory = bool(soubory)
        zapisovatelne = []
        for pk, uuid, nazev, mimetype in soubory:
            entry = placeholders.get(mimetype) if placeholders is not None else None
            if entry is None:
                logger.warning(
                    "core.management.commands.generate_metadata_fast.no_placeholder",
                    extra={"pk": pk, "mimetype": mimetype, "ident_cely": obj.ident_cely},
                )
                failures.append((pk, obj.ident_cely, f"Chybí placeholder pro mimetype '{mimetype}'."))
                continue
            zapisovatelne.append((pk, uuid, nazev, mimetype, entry))

        def zaeviduj_db_updates():
            """
            Zapíše soubory záznamu do ``db_updates`` pro pozdější ``_flush_db_updates``.

            Volá se **až** když je zápis do Fedory jistý (po commitu, nebo při kolizi slugu,
            kdy záznam ve Fedoře prokazatelně je z dřív zkomitovaného pokusu). Dřív se ``pk``
            přidávalo hned při vkládání souboru do transakce, takže záznam, který nakonec
            vyčerpal všechny pokusy, dostal do ``Soubor.sha_512``/``size_mb`` placeholder,
            který se do Fedory nikdy nedostal (review issue #3967).
            """
            if db_updates is None or not zapisovatelne:
                return
            with db_updates_lock:
                for pk_souboru, _uuid, _nazev, mimetype_souboru, _entry in zapisovatelne:
                    db_updates[mimetype_souboru].append(pk_souboru)

        attempt = 0
        while True:
            tx_url = None
            try:
                tx_url = writer.begin_transaction()
                writer.create_record(obj.ident_cely, model_name, document, hash512, tx_url=tx_url)
                if melo_soubory:
                    # Kontejner `/file` se zakládá podle toho, jestli záznam má soubory v DB,
                    # ne podle `zapisovatelne` - u záznamu, jehož všechny soubory nemají
                    # placeholder, tak zůstane chování stejné jako dřív (prázdný kontejner).
                    writer.create_file_container(obj.ident_cely, tx_url=tx_url)
                    for pk, uuid, nazev, mimetype, entry in zapisovatelne:
                        writer.create_binary_file(
                            obj.ident_cely,
                            uuid,
                            nazev,
                            mimetype,
                            entry["orig_bytes"],
                            entry["orig_sha512"],
                            entry["thumb_bytes"],
                            entry["thumb_sha512"],
                            entry["thumb_large_bytes"],
                            entry["thumb_large_sha512"],
                            tx_url=tx_url,
                        )
                writer.commit_transaction(tx_url)
                zaeviduj_db_updates()
                return
            except FedoraSlugCollision as exc:
                # Zaznam uz ve Fedore je - tenhle pokus byl zbytecny (typicky opakovani po
                # 409, jehoz commit ve skutecnosti prosel). Rollback zahodi rozdelanou
                # transakci i s prejmenovanym duplikatem, takze ve Fedore po nas nic
                # nezustane. Neni to chyba behu, jen se dal nepokousime.
                if tx_url:
                    writer.rollback_transaction(tx_url)
                # Fedora commituje transakce atomicky, takže dřívější pokus, který kolizi
                # způsobil, uložil záznam včetně všech jeho souborů - z pohledu DB je to
                # úspěch a `Soubor.sha_512`/`size_mb` se má přepsat.
                zaeviduj_db_updates()
                logger.warning(
                    "core.management.commands.generate_metadata_fast.uz_existuje",
                    extra={
                        "pk": obj.pk,
                        "ident_cely": obj.ident_cely,
                        "attempt": attempt,
                        "location": exc.location,
                    },
                )
                return
            except Exception as exc:
                if tx_url:
                    writer.rollback_transaction(tx_url)
                if not _is_retryable(exc):
                    logger.error(
                        "core.management.commands.generate_metadata_fast.record_failed",
                        extra={"pk": obj.pk, "ident_cely": obj.ident_cely, "error": str(exc)},
                    )
                    failures.append((obj.pk, obj.ident_cely, str(exc)))
                    return
                attempt += 1
                uplynulo = time.time() - zacatek
                if attempt > max_retries or uplynulo > _RECORD_TIME_BUDGET:
                    duvod = "vyčerpané pokusy" if attempt > max_retries else "vyčerpaný časový strop"
                    logger.error(
                        "core.management.commands.generate_metadata_fast.retries_exhausted",
                        extra={
                            "pk": obj.pk,
                            "ident_cely": obj.ident_cely,
                            "attempts": attempt,
                            "elapsed": round(uplynulo),
                            "reason": duvod,
                            "error": str(exc),
                        },
                    )
                    failures.append((obj.pk, obj.ident_cely, f"{duvod} ({attempt}. pokus): {exc}"))
                    return
                # Konflikt na sdíleném rodiči (409/410, viz _RETRYABLE_STATUS_CODES) se
                # sám o sobě nevyřeší rychle - potřebuje čas, ať se aktuálně běžící
                # konkurenční transakce na tomtéž kontejneru stihnou zkomitovat. Krátký
                # backoff (dřív max ~3,5 s součtem přes 3 pokusy) na to nestačil, proto
                # vyšší základ i strop a jitter škálovaný s backoffem samotným (ne pevných
                # 0-0,5 s) - ať se různá vlákna, co narazila na stejný konflikt zároveň,
                # při retry víc rozprostřou v čase místo opětovné kolize nastejno.
                base_backoff = min(60.0, 2.0 * (2 ** (attempt - 1)))
                backoff = base_backoff + random.uniform(0, base_backoff * 0.5)
                # Bez tohohle logu je opakování zcela neviditelne - v logu se objevi jen
                # vycerpane retries, takze uspesne opakovani (a tedy i pripadny duplikat,
                # ktery pri nem vznikne) projde jako ciste uspesny zaznam.
                logger.warning(
                    "core.management.commands.generate_metadata_fast.retry",
                    extra={
                        "pk": obj.pk,
                        "ident_cely": obj.ident_cely,
                        "attempt": attempt,
                        "backoff": round(backoff, 1),
                        "error": str(exc),
                    },
                )
                time.sleep(backoff)

    def _run_parallel(self, work_items, worker_fn, workers, total=None):
        """
        Spustí ``worker_fn`` nad ``work_items``, sekvenčně nebo paralelně přes vlákna.

        Průběh se počítá v položkách (jedna ``worker_fn(item)`` = jedna položka). Odhad
        zbývajícího času (ETA) vychází z průměrné rychlosti od začátku běhu (v rámci
        tohoto volání, tj. v rámci jednoho modelu).

        :param work_items: Iterátor položek k zpracování.
        :param worker_fn: Funkce volaná pro jednu položku (``worker_fn(item)``); návratová
            hodnota se ignoruje.
        :param workers: Počet paralelních vláken (1 = sekvenční zpracování).
        :param total: Celkový počet položek pro výpočet progressu a ETA (pokud je znám).
        """
        progress_lock = Lock()
        counter = {"done": 0}
        start_time = time.time()

        def report(done):
            elapsed = time.time() - start_time
            if total:
                percent = (done / total) * 100
                if done > 0 and elapsed > 1:
                    rate = done / elapsed
                    eta = _format_duration((total - done) / rate) if rate > 0 else "?"
                else:
                    eta = "?"
                self.stdout.write(f"\r{done}/{total} ({percent:.1f}%) - zbývá cca {eta}", ending="")
            else:
                self.stdout.write(f"\r{done}", ending="")
            self.stdout.flush()

        def worker(item):
            try:
                worker_fn(item)
            finally:
                close_old_connections()
            with progress_lock:
                counter["done"] += 1
                report(counter["done"])

        if not workers or workers <= 1:
            try:
                done = 0
                for item in work_items:
                    worker_fn(item)
                    done += 1
                    report(done)
            finally:
                close_old_connections()
            self.stdout.write("")
            return 0

        # Úlohy se odesílají průběžně, ne po uzavřených dávkách. Dřív tu bylo
        # `list(executor.map(worker, davka))`, což je bariéra: čekalo se na všech
        # `workers * _BATCH_PER_WORKER` položek dávky, takže jediná nedokončená úloha
        # zastavila celý běh, i když ostatní workeři byli volní (reálně se to stalo -
        # issue #3967, vlákno uvízlo v `getaddrinfo`). Počet rozpracovaných úloh je
        # přesto omezený, aby se queryset nemusel materializovat celý do paměti.
        limit = workers * _BATCH_PER_WORKER
        rozpracovane = {}
        zaseknutych = 0
        executor = ThreadPoolExecutor(max_workers=workers)

        def skliz():
            """Sklidí dokončené úlohy a opustí ty, které přesáhly ``_STUCK_TIMEOUT``."""
            nonlocal zaseknutych
            hotove, _ = wait(set(rozpracovane), timeout=_WATCHDOG_INTERVAL, return_when=FIRST_COMPLETED)
            for future in hotove:
                rozpracovane.pop(future, None)
                vyjimka = future.exception()
                if vyjimka is not None:
                    # _process_record si chyby řeší sám, sem se dostane jen něco
                    # nečekaného - ať to nezmizí.
                    logger.error(
                        "core.management.commands.generate_metadata_fast.worker_failed",
                        extra={"error": str(vyjimka)},
                    )
            nyni = time.time()
            for future, (polozka, odeslano) in list(rozpracovane.items()):
                if nyni - odeslano <= _STUCK_TIMEOUT:
                    continue
                # Vlákno zaseknuté v systémovém volání se z Pythonu ukončit nedá, takže
                # ho jen přestaneme sledovat - přijdeme o jeden worker, ne o celý běh.
                rozpracovane.pop(future, None)
                zaseknutych += 1
                logger.error(
                    "core.management.commands.generate_metadata_fast.uloha_zaseknuta",
                    extra={
                        "pk": getattr(polozka, "pk", None),
                        "ident_cely": getattr(polozka, "ident_cely", None),
                        "elapsed": round(nyni - odeslano),
                    },
                )
                self.stdout.write("")
                self.stdout.write(
                    self.style.ERROR(
                        f"Zaseknutá úloha po {round(nyni - odeslano)}s opuštěna: "
                        f"{getattr(polozka, 'ident_cely', getattr(polozka, 'pk', '?'))} "
                        "(vlákno zůstane blokované, běh pokračuje)"
                    )
                )

        try:
            for item in work_items:
                rozpracovane[executor.submit(worker, item)] = (item, time.time())
                while len(rozpracovane) >= limit:
                    skliz()
            while rozpracovane:
                skliz()
        finally:
            # wait=False: kdyby některé vlákno uvízlo, shutdown(wait=True) by tu čekal
            # navždy. Zbylé úlohy jsou v tu chvíli buď hotové, nebo opuštěné watchdogem.
            executor.shutdown(wait=False)
            if zaseknutych:
                # ThreadPoolExecutor registruje atexit hook, který na konci procesu
                # join-uje své workery - tímto se ten join přeskočí. Samo to ale NESTAČÍ:
                # workery jsou non-daemon vlákna, takže je při ukončení joinuje i samotný
                # interpret. Proto se běh na konci ukončuje natvrdo, viz `handle`.
                concurrent.futures.thread._threads_queues.clear()
            close_old_connections()

        self.stdout.write("")
        if zaseknutych:
            self.stdout.write(
                self.style.ERROR(
                    f"Opuštěno {zaseknutych} zaseknutých úloh - tyto záznamy ve Fedoře chybí "
                    "a odhalí je závěrečná kontrola konzistence."
                )
            )
        return zaseknutych

    def _handle_metadata(self, options, writer, placeholders):
        """
        Zpracuje XML metadata a (pokud záznam nějaké má) i jeho soubory ve stejné transakci.

        :param options: Parametry příkazu.
        :param writer: Sdílený ``_FastFedoraWriter`` (repozitář už byl ověřen jako prázdný).
        :param placeholders: Mapa mimetype -> placeholder obsah (``_load_placeholders``),
            nebo ``None`` při ``--bez-souboru`` - viz ``_process_record``.
        """
        self._zaseknute_ulohy = 0
        self._pocet_selhani = 0
        model_class = options.get("model")
        limit = options.get("limit")
        start_with_pk = options.get("start_with_pk")
        workers = options.get("workers") or 1
        max_retries = options.get("max_retries") or 3
        aktualizovat_db = bool(options.get("aktualizovat_db"))
        schema_by_name = _get_schema_by_name()

        if not model_class:
            # Bez --model se --start-with-pk aplikuje stejně na všech 15 modelů (stejné
            # chování jako u generate_metadata) - jako navázání po pádu dává smysl jen
            # pro model, na kterém běh spadl; pro ostatní se tím zbytečně přeskočí
            # záznamy s nižším pk. Použij --start-with-pk vždy spolu s --model.
            for current_class, _fedora_name in schema_by_name.values():
                queryset = current_class.objects.all().order_by("pk")
                if start_with_pk:
                    queryset = current_class.objects.filter(pk__gte=start_with_pk).order_by("pk")
                total = queryset.count()
                if limit is not None:
                    queryset = queryset[:limit]
                    total = min(total, limit)
                self.stdout.write(f"== {current_class.__name__} ({total}) ==")
                failures = []
                # db_updates/lock jsou nové pro každý model - _flush_db_updates se volá
                # hned po doběhnutí (ne až na konci celého běhu), ať se dopad případného
                # pádu na aktualizaci DB omezí na jeden rozpracovaný model, ne na celý běh.
                db_updates = defaultdict(list) if aktualizovat_db else None
                db_updates_lock = Lock() if aktualizovat_db else None
                self._zaseknute_ulohy += self._run_parallel(
                    queryset.iterator(chunk_size=500),
                    lambda obj: self._process_record(
                        obj, writer, max_retries, failures, placeholders, db_updates, db_updates_lock
                    ),
                    workers,
                    total=total,
                )
                self._report_failures(failures)
                self._pocet_selhani += len(failures)
                self._flush_db_updates(db_updates, db_updates_lock, placeholders)
        else:
            entry = schema_by_name.get(model_class)
            if entry is None:
                raise CommandError(
                    f"Neznámý model '{model_class}'. Platné hodnoty: {', '.join(sorted(schema_by_name))}."
                )
            model_cls = entry[0]
            queryset = model_cls.objects.order_by("pk").all()
            if start_with_pk:
                queryset = model_cls.objects.filter(pk__gte=start_with_pk).order_by("pk")
            if limit is not None:
                queryset = queryset[:limit]
            total = queryset.count()
            failures = []
            db_updates = defaultdict(list) if aktualizovat_db else None
            db_updates_lock = Lock() if aktualizovat_db else None
            self._zaseknute_ulohy += self._run_parallel(
                queryset.iterator(chunk_size=500),
                lambda obj: self._process_record(
                    obj, writer, max_retries, failures, placeholders, db_updates, db_updates_lock
                ),
                workers,
                total=total,
            )
            self._report_failures(failures)
            self._pocet_selhani += len(failures)
            self._flush_db_updates(db_updates, db_updates_lock, placeholders)

    @staticmethod
    def _identy_z_db(queryset):
        """
        Vrátí množinu ``ident_cely`` pro queryset.

        Většina modelů má ``ident_cely`` jako databázový sloupec, takže se čte jedním
        ``values_list``. U ``RuianKraj``/``RuianOkres`` je to ale Python property (ne
        pole), takže tam ``values_list`` skončí ``FieldError`` a musí se iterovat přes
        instance.

        :param queryset: Queryset modelu.

            :return: Množina identifikátorů.
        """
        from django.core.exceptions import FieldDoesNotExist

        try:
            queryset.model._meta.get_field("ident_cely")
        except FieldDoesNotExist:
            return {obj.ident_cely for obj in queryset if obj.ident_cely}
        return {i for i in queryset.values_list("ident_cely", flat=True) if i}

    def _zkontroluj_konzistenci(self, options, writer):
        """
        Po dogenerování porovná, co je v DB, s tím, co je ve Fedoře, a vypíše rozdíly.

        Hledá dvě věci, které se při běhu na statisících záznamů reálně staly (issue #3967):

        - **chybí ve Fedoře** - záznam je v DB, ale zápis selhal (vyčerpané retries, trvalá
          chyba). Ve ``failures`` se sice objeví, ale ty se vypisují po každém modelu zvlášť
          a v dlouhém logu snadno zapadnou.
        - **navíc ve Fedoře** - zdroj, který nemá protějšek v DB. Typicky duplikát z retry:
          když Fedora ohlásí chybu na commitu, který fakticky prošel, opakování narazí na
          kolizi ``Slug`` a Fedora zdroj přejmenuje na náhodné UUID. Tohle je nejzákeřnější
          případ, protože záznam se přitom zaloguje jako úspěšný.

        Porovnává se přes ``/model/{model}/member`` (link zdroje), protože ty jsou 1:1 se
        záznamy. Použijí se stejné filtry (``--model``/``--limit``/``--start-with-pk``) jako
        při generování, aby srovnání dávalo smysl i u částečného běhu.

        :param options: Parametry příkazu.
        :param writer: Sdílený ``_FastFedoraWriter``.

            :return: ``True``, pokud je vše konzistentní, jinak ``False``.
        """
        model_class = options.get("model")
        limit = options.get("limit")
        start_with_pk = options.get("start_with_pk")
        schema_by_name = _get_schema_by_name()

        if model_class:
            polozky = [(model_class, schema_by_name[model_class])]
        else:
            polozky = list(schema_by_name.items())

        self.stdout.write("")
        self.stdout.write("=== Kontrola konzistence DB vs Fedora ===")
        self.stdout.write(f"{'model':<24}{'DB':>9}{'Fedora':>9}{'chybí':>8}{'navíc':>8}")

        vse_chybi = []
        vse_navic = []
        for nazev_tridy, (current_class, fedora_name) in polozky:
            queryset = current_class.objects.all().order_by("pk")
            if start_with_pk:
                queryset = current_class.objects.filter(pk__gte=start_with_pk).order_by("pk")
            if limit is not None:
                queryset = queryset[:limit]
            db_identy = self._identy_z_db(queryset)
            try:
                fedora_identy = writer.list_model_members(fedora_name)
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"{nazev_tridy:<24} kontrola selhala: {exc}"))
                continue

            chybi = db_identy - fedora_identy
            # Při --limit/--start-with-pk je "navíc" nevypovídající (ve Fedoře je legitimně
            # víc, než kolik jsme právě zpracovali), proto se počítá jen u plného běhu.
            navic = (fedora_identy - db_identy) if (limit is None and not start_with_pk) else set()

            styl = self.style.ERROR if (chybi or navic) else self.style.SUCCESS
            self.stdout.write(
                styl(f"{nazev_tridy:<24}{len(db_identy):>9}{len(fedora_identy):>9}" f"{len(chybi):>8}{len(navic):>8}")
            )
            vse_chybi.extend((nazev_tridy, i) for i in sorted(chybi))
            vse_navic.extend((nazev_tridy, i) for i in sorted(navic))

        if vse_chybi:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR(f"CHYBÍ ve Fedoře ({len(vse_chybi)}) - v DB je, zápis neproběhl:"))
            for nazev_tridy, ident in vse_chybi[:50]:
                self.stdout.write(self.style.ERROR(f"  {nazev_tridy}: {ident}"))
            if len(vse_chybi) > 50:
                self.stdout.write(self.style.ERROR(f"  ... a dalších {len(vse_chybi) - 50}"))

        if vse_navic:
            self.stdout.write("")
            self.stdout.write(
                self.style.ERROR(
                    f"NAVÍC ve Fedoře ({len(vse_navic)}) - nemá protějšek v DB, "
                    "typicky duplikát z opakování (Fedora přejmenovala kolidující Slug na UUID):"
                )
            )
            for nazev_tridy, ident in vse_navic[:50]:
                self.stdout.write(self.style.ERROR(f"  {nazev_tridy}: {ident}"))
            if len(vse_navic) > 50:
                self.stdout.write(self.style.ERROR(f"  ... a dalších {len(vse_navic) - 50}"))

        if not vse_chybi and not vse_navic:
            self.stdout.write(self.style.SUCCESS("Vše sedí - žádné chybějící ani přebývající záznamy."))
            return True
        return False

    def _report_failures(self, failures):
        """
        Vypíše souhrn selhaných položek (pokud nějaké jsou) po doběhnutí ``_run_parallel``.

        Selhání sama o sobě běh nezastaví (viz ``_process_record``)
        - tenhle souhrn je jediné místo, kde se na ně dá přijít, proto obsahuje i prvních
        pár konkrétních identů/pk pro dohledání.

        :param failures: Seznam n-tic ``(pk_nebo_ident, ident_cely_nebo_None, chyba)``.
        """
        if not failures:
            return
        self.stdout.write(self.style.ERROR(f"Selhalo {len(failures)} položek:"))
        for item in failures[:20]:
            self.stdout.write(self.style.ERROR(f"  {item[0]} ({item[1]}): {item[2][:200]}"))
        if len(failures) > 20:
            self.stdout.write(self.style.ERROR(f"  ... a dalších {len(failures) - 20} (viz log)."))

    def handle(self, *args, **options):
        """
        Spustí generování XML metadat (a souborů, pokud záznam nějaké má) do Fedory.

        Nejdřív se ověří placeholder_manifest.json (pokud není ``--bez-souboru``) -
        manifest i všechny placeholder soubory, na které odkazuje, se musí dát načíst
        (viz ``_load_placeholders``); pokud ne, příkaz skončí hned na začátku bez
        jakéhokoli zápisu do Fedory. Pak se jedním dotazem ověří, že ``/record`` v
        repozitáři neobsahuje žádný záznam - viz docstring třídy. Tím odpadá nutnost
        kontrolovat existenci každého jednotlivého containeru zvlášť (což by běh
        výrazně zpomalilo), za cenu toho, že příkaz není idempotentní - nelze ho
        bezpečně spustit dvakrát nad stejným (byť částečně naplněným) repozitářem.

        :param args: Poziční argumenty příkazu (nepoužívá se).
        :param options: Pojmenované argumenty ze příkazového řádku.

            :raises CommandError: Pokud (bez ``--bez-souboru``) nejde načíst
                placeholder_manifest.json, nebo pokud ``/record`` už obsahuje
                nějaký záznam (bez ``--force``).
        """
        if options.get("jen_kontrola"):
            if not self._zkontroluj_konzistenci(options, self._get_writer()):
                raise CommandError("Kontrola konzistence našla nesrovnalosti (podrobnosti výše).")
            return

        placeholders = None
        if not options.get("bez_souboru"):
            try:
                placeholders = _load_placeholders()
            except (OSError, ValueError, KeyError) as exc:
                raise CommandError(
                    f"Placeholder manifest '{_PLACEHOLDER_MANIFEST_PATH}' se nepodařilo načíst ({exc}). "
                    "Oprav placeholdery, nebo spusť s --bez-souboru, pokud soubory opravdu generovat nechceš."
                )

        writer = self._get_writer()
        if options.get("force"):
            self.stdout.write(self.style.WARNING("--force: kontrola prázdnosti /record se přeskakuje."))
        elif not writer.is_repository_empty():
            raise CommandError(
                "Repozitář /record už obsahuje záznamy - generate_metadata_fast není idempotentní "
                "a smí běžet jen nad prázdnou Fedorou. Pro navázání po pádu spusť znovu s "
                "--force a --start-with-pk nastaveným za poslední úspěšně zpracovaný záznam."
            )
        self._handle_metadata(options, writer, placeholders)

        konzistentni = True
        if not options.get("bez_kontroly"):
            konzistentni = self._zkontroluj_konzistenci(options, writer)

        # Běh, ve kterém něco selhalo, nesmí skončit nulovým exit kódem - jinak ho volající
        # skript (nebo orchestrace 24h produkčního běhu) vyhodnotí jako úspěch, i když část
        # záznamů ve Fedoře chybí. Návratová hodnota kontroly konzistence se dřív zahazovala
        # a selhání jednotlivých záznamů se nikde neprojevila (review issue #3967).
        problemy = []
        if self._pocet_selhani:
            problemy.append(f"{self._pocet_selhani} položek selhalo")
        if not konzistentni:
            problemy.append("kontrola konzistence našla nesrovnalosti")
        if self._zaseknute_ulohy:
            problemy.append(f"{self._zaseknute_ulohy} vláken zůstalo zaseknutých")

        if self._zaseknute_ulohy:
            # Uvízlé vlákno je non-daemon, takže by na něj interpret při ukončení čekal
            # navěky (u syscallu, ze kterého se nevrátí). Veškerá práce i kontrola jsou
            # v tuhle chvíli hotové, takže proces ukončíme natvrdo - jinak by to vypadalo
            # jako další zásek. `os._exit` obchází i vyhazování `CommandError` níže, proto
            # se exit kód předává přímo.
            self.stdout.write(
                self.style.WARNING(
                    f"Ukončuji natvrdo - {self._zaseknute_ulohy} vláken zůstalo zaseknutých "
                    "v systémovém volání a nelze je ukončit."
                )
            )
            self.stdout.write(self.style.ERROR("Běh nedokončen bez chyb: " + ", ".join(problemy) + "."))
            self.stdout.flush()
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(1)

        if problemy:
            raise CommandError("Běh dokončen s chybami: " + ", ".join(problemy) + " (podrobnosti viz log).")
