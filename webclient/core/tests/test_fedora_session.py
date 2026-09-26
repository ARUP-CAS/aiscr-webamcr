"""
Testy izolace Fedora ``requests.Session`` mezi vlákny.

``requests.Session`` není thread-safe – nese mutable stav, především cookie
jar. Fedora (Tomcat + Shiro) po přihlášení vrací cookie ``JSESSIONID``, takže
při session sdílené mezi vlákny si ji vlákna mohou navzájem přepsat a request
pak odejde s identifikátorem servletové session, kterou už Shiro nemusí uznat.
``generate_metadata --workers`` přitom posílá requesty z několika vláken.

Connection pool naopak sdílený zůstat **má**: ``urllib3.PoolManager`` je
thread-safe a sdružené sockety drží nízký počet otevíraných TCP spojení.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

from core.repository_connector import (
    FedoraRepositoryConnector,
    FedoraRequestType,
    _fedora_adapter,
    _get_fedora_session,
    _thread_local,
)
from django.test import SimpleTestCase


class FedoraSessionThreadLocalTests(SimpleTestCase):
    """Testy, že každé vlákno dostane vlastní session nad společným poolem."""

    def setUp(self):
        """Zahodí session hlavního vlákna, ať testy nezávisí na pořadí."""
        for atribut in ("session", "admin_session"):
            if hasattr(_thread_local, atribut):
                delattr(_thread_local, atribut)

    def test_stejne_vlakno_dostane_tutez_session(self):
        """Opakované volání v jednom vláknu nezakládá novou session."""
        self.assertIs(_get_fedora_session(), _get_fedora_session())

    def test_identity_maji_oddelene_session(self):
        """
        Běžná a admin identita nesmí sdílet cookie jar.

        Jinak by ``JSESSIONID`` přenesla do admin požadavku subjekt přihlášený
        jako ``FEDORA_USER`` a mazání tombstone by skončilo na HTTP 403.
        """
        self.assertIsNot(_get_fedora_session(), _get_fedora_session(admin=True))

    def test_kazde_vlakno_ma_vlastni_session(self):
        """
        Osm souběžných vláken dostane osm různých session objektů.

        Bariéra je nutná: bez ní by pool krátké úlohy oběhl několika málo
        vlákny a test by porovnával session recyklovaných vláken. Reference
        se drží po celou dobu, aby ``id()`` nemohlo připadnout jinému objektu.
        """
        pocet = 8
        pripraveno = threading.Barrier(pocet, timeout=5)

        def zisk(_):
            session = _get_fedora_session()
            pripraveno.wait()
            return session

        with ThreadPoolExecutor(max_workers=pocet) as pool:
            session = list(pool.map(zisk, range(pocet)))

        self.assertEqual(len({id(s) for s in session}), pocet, "vlákna sdílejí session")

    def test_cookie_jar_neni_sdileny(self):
        """
        Cookie nastavená v jednom vláknu se nesmí objevit v druhém.

        Tohle je jádro nálezu F11 – přesně takhle si vlákna přepisovala
        ``JSESSIONID``.
        """
        pripraveno = threading.Barrier(2)
        nalezeno = []

        def vlakno(jmeno):
            session = _get_fedora_session()
            session.cookies.set("JSESSIONID", f"session-{jmeno}")
            pripraveno.wait(timeout=5)
            nalezeno.append((jmeno, session.cookies.get("JSESSIONID")))

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(vlakno, ["A", "B"]))

        self.assertEqual(sorted(nalezeno), [("A", "session-A"), ("B", "session-B")])

    def test_pool_zustava_sdileny(self):
        """
        Adapter (a tím i pool socketů) je pro všechna vlákna společný.

        Kdyby si každé vlákno stavělo vlastní pool, násobil by se počet
        otevíraných TCP spojení – právě tomu má sdružený pool bránit.
        """
        with ThreadPoolExecutor(max_workers=4) as pool:
            adaptery = list(pool.map(lambda _: id(_get_fedora_session().get_adapter("http://x/")), range(4)))

        self.assertEqual(set(adaptery), {id(_fedora_adapter)})

    def test_vyber_session_podle_typu_pozadavku(self):
        """Admin typy požadavků sáhnou po admin session, ostatní po běžné."""
        vybrana = FedoraRepositoryConnector._get_session(FedoraRequestType.CREATE_CONTAINER)

        self.assertIs(vybrana, _get_fedora_session())
        self.assertIsNot(vybrana, _get_fedora_session(admin=True))
