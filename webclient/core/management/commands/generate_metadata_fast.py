import functools
import hashlib
import json
import logging
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Lock

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from django.utils.translation import gettext as _
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

_RETRYABLE_EXCEPTIONS = (requests.exceptions.ConnectionError, requests.exceptions.Timeout)

#: HTTP status kódy z Fedory, které se považují za přechodné (stojí za retry) - server
#: chyby (5xx, typicky přetížení/konflikt při souběžném zápisu do stejného sdíleného
#: rodiče, např. `/model/{model}/member`), 409 Conflict a 410 Gone (Fedora transakce má
#: timeout - výchozí 3 minuty - a záznam s hodně soubory drží jednu transakci celou
#: dobu jeho zpracování; po expiraci transakce vrátí 410 na každý další request v ní.
#: Rollback v ``_process_record`` proběhne bez efektu - transakce už neexistuje - takže
#: samotné opakování celého záznamu v nové transakci je bezpečné). Cokoli jiného (4xx)
#: je považováno za trvalou chybu naší strany a neopakuje se.
_RETRYABLE_STATUS_CODES = {409, 410, 500, 502, 503, 504}

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

        :param base_url: Základní URL Fedora repozitáře (``.../rest/{FEDORA_SERVER_NAME}``).
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
            self._thread_local.admin_session = session
        return session

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
        response = getattr(self._session(), method)(url, headers=headers, data=data, verify=False)
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
        response = self._session().post(url, verify=False)
        if not str(response.status_code).startswith("2"):
            raise FastFedoraWriteError(url, response.status_code, response.text)
        match = re.search(
            r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", response.headers.get("Location", "")
        )
        if not match:
            raise FastFedoraWriteError(url, response.status_code, "Location header neobsahuje ID transakce.")
        return f"{self.rest_root}/fcr:tx/{match.group()}"

    def commit_transaction(self, tx_url: str):
        """
        Potvrdí transakci - všechny mutace provedené s touto ``Atomic-ID`` se sbalí do
        jedné nové OCFL verze na dotčený objekt (viz docstring třídy).

        :param tx_url: URL transakce z ``begin_transaction``.

            :raises FastFedoraWriteError: Pokud commit selže.
        """
        response = self._admin_session().put(tx_url, verify=False)
        if not str(response.status_code).startswith("2"):
            raise FastFedoraWriteError(tx_url, response.status_code, response.text)

    def rollback_transaction(self, tx_url: str):
        """
        Zruší transakci (best-effort - chyba při rollbacku se jen zaloguje, ať
        nepřekryje původní chybu, kvůli které se rollback volá).

        :param tx_url: URL transakce z ``begin_transaction``.
        """
        try:
            self._admin_session().delete(tx_url, verify=False)
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "core.management.commands.generate_metadata_fast.rollback_failed",
                extra={"tx_url": tx_url, "error": str(exc)},
            )

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
        self._request(
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
        link_url = f"{self.base_url}/model/{model_name}/member"
        self._request(
            "post",
            link_url,
            {"Slug": ident_cely, "Content-Type": "text/turtle"},
            "@prefix ore: <http://www.openarchives.org/ore/terms/> . "
            "@prefix dcterms: <http://purl.org/dc/terms/> . "
            f"<> ore:proxyFor <info:fedora/{self.server_name}/record/{ident_cely}> ; "
            f"dcterms:creator <info:fedora/{self.server_name}/record/{self.user_ident}> .",
            tx_url=tx_url,
        )
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

    def is_repository_empty(self):
        """
        Ověří, že ``/record`` kolekce v repozitáři neobsahuje žádný záznam.

        Nahrazuje kontrolu existence jednotlivých containerů (ta by běh výrazně
        zpomalila) jedním rychlým dotazem na začátku běhu - viz docstring ``Command``.

        Odpověď se žádá v ``application/n-triples`` (ne ``text/turtle``) záměrně -
        n-triples serializace nepoužívá prefixy, takže se v textu vždy objeví plné
        ``http://www.w3.org/ns/ldp#contains`` URI. Kontrola na ``"ldp:contains"`` by
        záludně záviselo na tom, že fcrepo zvolí zrovna tenhle turtle prefix.

        :return: ``True``, pokud ``/record`` neobsahuje žádný ``ldp:contains`` triple
            (nebo vůbec neexistuje), jinak ``False``.

            :raises FastFedoraWriteError: Pokud dotaz vrátí jiný status kód než 200/404.
        """
        response = self._session().get(
            f"{self.base_url}/record", headers={"Accept": "application/n-triples"}, verify=False
        )
        if response.status_code == 404:
            return True
        if response.status_code != 200:
            raise FastFedoraWriteError(f"{self.base_url}/record", response.status_code, response.text)
        return "http://www.w3.org/ns/ldp#contains" not in response.text

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

    SHA-512 hash se vždy počítá znovu z přečtených bajtů - hodnota v manifestu slouží
    jen jako kontrola (neshoda se zaloguje jako WARNING, ale načtení nespadne). Nejde
    o přílišnou opatrnost: `.gitattributes` (`* text=auto`) normalizuje konce řádků
    textových placeholderů (`.csv`/`.txt`) při checkoutu, takže hash zapsaný do
    manifestu na jiném OS/checkoutu neodpovídá aktuálním bajtům na disku - ověřeno
    (issue #3967 review) na `placeholder_19.csv` (20 B v manifestu, 22 B na Windows
    checkoutu s CRLF). Kdyby se poslal `Digest: sha-512=<manifest>` neodpovídající
    tělu požadavku, Fedora by na každý takový soubor vracela 409.

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
    odpovídající vloženému placeholderu (viz ``_aktualizuj_soubory_v_db``). Bez něj
    zůstane DB ukazovat hash/velikost původního souboru, který ale ve Fedoře není -
    což může být žádoucí, pokud se DB řeší jinak (odsud opt-in, ne výchozí chování).

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
            default=3,
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
            "--aktualizovat-db",
            action="store_true",
            default=False,
            help=(
                "Po úspěšném vložení placeholderu do Fedory přepíše Soubor.sha_512/size_mb "
                "v DB na hodnoty odpovídající vloženému placeholderu (ne původnímu, skutečnému "
                "souboru) - bez toho DB po migraci ukazuje hash/velikost obsahu, který ve "
                "Fedoře reálně není. Nemá efekt bez --bez-souboru vynechaných souborů. "
                "Mutuje DB hromadně - použij vědomě, ne jen 'pro jistotu'."
            ),
        )

    @staticmethod
    def _get_writer():
        """
        Vytvoří ``_FastFedoraWriter`` napojený na aktuálně nakonfigurovanou Fedoru.

        :return: Instance ``_FastFedoraWriter``.
        """
        from core.log_middleware import LogMiddleware
        from django.conf import settings

        base_url = (
            f"{settings.FEDORA_PROTOCOL}://{settings.FEDORA_SERVER_HOSTNAME}:{settings.FEDORA_PORT_NUMBER}"
            f"/rest/{settings.FEDORA_SERVER_NAME}"
        )
        return _FastFedoraWriter(base_url, LogMiddleware.get_user_id())

    @staticmethod
    def _aktualizuj_soubory_v_db(zapsane):
        """
        Přepíše ``Soubor.sha_512``/``size_mb`` v DB na hodnoty odpovídající placeholderu,
        který byl skutečně vložen do Fedory (viz ``--aktualizovat-db`` a "Poznámka k
        záměru" v review issue #3967).

        Migrace vědomě nahrazuje obsah souborů placeholdery - bez tohoto kroku by
        ``Soubor.sha_512``/``size_mb`` v DB dál odpovídaly původnímu (skutečnému)
        souboru, který ale ve Fedoře reálně není. Krok je opt-in (``--aktualizovat-db``),
        protože jde o hromadnou mutaci produkční DB, ne jen zápis do Fedory.

        :param zapsane: Seznam ``(pk, entry)`` - ``entry`` je položka z ``_load_placeholders``
            odpovídající placeholderu skutečně zapsanému pro tento ``Soubor.pk``.
        """
        from core.models import Soubor

        for pk, entry in zapsane:
            Soubor.objects.filter(pk=pk).update(
                sha_512=entry["orig_sha512"],
                size_mb=Decimal(len(entry["orig_bytes"])) / Decimal(1_000_000),
            )

    @staticmethod
    def _process_record(obj, writer, max_retries, failures, placeholders=None, aktualizovat_db=False):
        """
        Vygeneruje XML metadata pro jeden záznam a vloží je do Fedory rychlou cestou.

        Pokud má záznam vlastní soubory (``Projekt``/``Dokument``/``SamostatnyNalez`` -
        viz ``obj.soubory``) a je předaný ``placeholders`` (načtený manifest, viz
        ``_load_placeholders``), vloží se **ve stejné transakci** jako metadata. Soubory
        jsou totiž potomci téže Fedora ArchivalGroup jako container/metadata daného
        záznamu - kdyby se zpracovaly v jiné transakci, vznikla by na tomtéž OCFL
        objektu druhá verze navíc (viz docstring ``_FastFedoraWriter`` a issue #3967 -
        měření ukázalo, že počet OCFL verzí určuje počet transakcí, ne počet mutací v nich).

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
        :param aktualizovat_db: Viz ``--aktualizovat-db`` - po úspěšném commitu přepíše
            ``Soubor.sha_512``/``size_mb`` vložených souborů na hodnoty placeholderu.
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
        attempt = 0
        while True:
            tx_url = None
            try:
                document = DocumentGenerator(obj).generate_document()
                hash512 = hashlib.sha512(document).hexdigest()
                tx_url = writer.begin_transaction()
                writer.create_record(obj.ident_cely, model_name, document, hash512, tx_url=tx_url)
                zapsane_soubory = []
                if placeholders is not None and isinstance(getattr(obj, "soubory", None), SouborVazby):
                    soubory = [
                        (s.pk, s.path.rsplit("/", 1)[-1], s.nazev, s.mimetype)
                        for s in obj.soubory.soubory.exclude(path="").exclude(path__isnull=True)
                    ]
                    if soubory:
                        writer.create_file_container(obj.ident_cely, tx_url=tx_url)
                        for pk, uuid, nazev, mimetype in soubory:
                            entry = placeholders.get(mimetype)
                            if entry is None:
                                logger.warning(
                                    "core.management.commands.generate_metadata_fast.no_placeholder",
                                    extra={"pk": pk, "mimetype": mimetype, "ident_cely": obj.ident_cely},
                                )
                                failures.append((pk, obj.ident_cely, f"Chybí placeholder pro mimetype '{mimetype}'."))
                                continue
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
                            zapsane_soubory.append((pk, entry))
                writer.commit_transaction(tx_url)
                if aktualizovat_db and zapsane_soubory:
                    Command._aktualizuj_soubory_v_db(zapsane_soubory)
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
                if attempt > max_retries:
                    logger.error(
                        "core.management.commands.generate_metadata_fast.retries_exhausted",
                        extra={"pk": obj.pk, "ident_cely": obj.ident_cely, "attempts": attempt, "error": str(exc)},
                    )
                    failures.append((obj.pk, obj.ident_cely, str(exc)))
                    return
                backoff = min(30.0, 0.5 * (2 ** (attempt - 1))) + random.uniform(0, 0.5)
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

        try:
            if workers and workers > 1:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    for davka in _po_davkach(work_items, workers * _BATCH_PER_WORKER):
                        list(executor.map(worker, davka))
            else:
                done = 0
                for item in work_items:
                    worker_fn(item)
                    done += 1
                    report(done)
        finally:
            close_old_connections()
        self.stdout.write("")

    def _handle_metadata(self, options, writer, placeholders):
        """
        Zpracuje XML metadata a (pokud záznam nějaké má) i jeho soubory ve stejné transakci.

        :param options: Parametry příkazu.
        :param writer: Sdílený ``_FastFedoraWriter`` (repozitář už byl ověřen jako prázdný).
        :param placeholders: Mapa mimetype -> placeholder obsah (``_load_placeholders``),
            nebo ``None`` při ``--bez-souboru`` - viz ``_process_record``.
        """
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
                self._run_parallel(
                    queryset.iterator(chunk_size=500),
                    lambda obj: self._process_record(obj, writer, max_retries, failures, placeholders, aktualizovat_db),
                    workers,
                    total=total,
                )
                self._report_failures(failures)
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
            self._run_parallel(
                queryset.iterator(chunk_size=500),
                lambda obj: self._process_record(obj, writer, max_retries, failures, placeholders, aktualizovat_db),
                workers,
                total=total,
            )
            self._report_failures(failures)

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
