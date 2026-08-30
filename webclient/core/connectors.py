import contextlib
import re
import socket
import struct
import sys
from io import BytesIO

from django.conf import settings
from django.utils.encoding import force_str

import redis
from webclient.settings.base import get_plain_redis_pass

# Regulární výraz pro parsování odpovědí ze skenování
scan_response = re.compile(r"^(?P<path>.*): ((?P<virus>.+) )?(?P<status>(FOUND|OK|ERROR))$")


class RedisConnector:
    """Implementuje komponentu ``RedisConnector`` v rámci aplikace."""

    r = None
    r_decode = None
    IMPORT_DATA_LOCK_KEY = "import_data_lock"
    # Zpětný odkaz lock → job_id: jediný singleton klíč (bez ``_{job_id}`` sufixu), který drží
    # id právě běžící importní úlohy. Umožňuje superuživateli ručně resetovat zaseklou úlohu i
    # z „import běží (jiný admin)“ stránky, kde stránka zná jen existenci locku, nikoli job_id.
    IMPORT_DATA_ACTIVE_JOB_KEY = "import_data_active_job_id"
    _RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""
    _REFRESH_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
end
return 0
"""
    _PERSIST_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('persist', KEYS[1])
else
    return 0
end
"""
    # Atomic phase/validity check + lock refresh, so two concurrent Start requests can't both
    # observe awaiting_approval and dispatch the import task twice.
    _CLAIM_AWAITING_IMPORT_SCRIPT = """
if redis.call("get", KEYS[1]) ~= ARGV[1] then
    return {0, ""}
end
if redis.call("get", KEYS[2]) ~= "1" then
    return {0, ""}
end
local token = redis.call("get", KEYS[3])
if not token or redis.call("get", KEYS[4]) ~= token then
    return {0, ""}
end
redis.call("set", KEYS[1], ARGV[2])
redis.call("expire", KEYS[4], ARGV[3])
return {1, token}
"""
    # Cancel has the same ownership boundary as Start.  It must not observe
    # awaiting_approval and then race a Start request which has already claimed
    # the job.
    _CANCEL_AWAITING_IMPORT_SCRIPT = """
if redis.call("get", KEYS[1]) ~= ARGV[1] then return 0 end
local token = redis.call("get", KEYS[2])
if not token or redis.call("get", KEYS[3]) ~= token then return 0 end
redis.call("set", KEYS[1], ARGV[2])
redis.call("set", KEYS[4], ARGV[3])
redis.call("del", KEYS[3])
if redis.call("get", KEYS[5]) == ARGV[4] then redis.call("del", KEYS[5]) end
if redis.call("get", KEYS[6]) == ARGV[4] then redis.call("del", KEYS[6]) end
return 1
"""
    _FINALIZE_VALIDATION_SCRIPT = """
if redis.call("get", KEYS[1]) ~= ARGV[1] then return 0 end
if redis.call("exists", KEYS[2]) ~= 0 then return 0 end
local token = redis.call("get", KEYS[3])
if not token or redis.call("get", KEYS[4]) ~= token then return 0 end
redis.call("set", KEYS[1], ARGV[2])
redis.call("persist", KEYS[4])
return 1
"""

    @classmethod
    def _create_connection(cls):
        """
        Vytvoří connection.

        :return: Nově vytvořená hodnota připravená touto funkcí.
        """
        cls.r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=get_plain_redis_pass())

    # Tento konektor vrací přímo řetězec, takže není potřeba volat `decode("utf-8")`.
    @classmethod
    def _create_connection_decode(cls):
        """
        Vytvoří connection decode.

        :return: Nově vytvořená hodnota připravená touto funkcí.
        """
        cls.r_decode = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=get_plain_redis_pass(), decode_responses=True
        )

    @classmethod
    def get_connection(cls) -> redis.Redis:
        """
        Vrací connection. v aplikaci.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        if not cls.r:
            cls._create_connection()
        return cls.r

    @classmethod
    def get_connection_decode(cls) -> redis.Redis:
        """
        Vrací connection decode.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        if not cls.r_decode:
            cls._create_connection_decode()
        return cls.r_decode

    @classmethod
    def acquire_import_lock(cls, connection: redis.Redis, token: str, ttl_seconds: int) -> bool:
        """
        Atomicky získá Redis lock pro běžící hromadný import.

        :param connection: Redis spojení, přes které se lock zapisuje.
        :param token: Jedinečný token vlastníka locku.
        :param ttl_seconds: Doba expirace locku v sekundách.
        :return: ``True``, pokud byl lock získán; jinak ``False``.
        """
        return bool(connection.set(cls.IMPORT_DATA_LOCK_KEY, token, nx=True, ex=ttl_seconds))

    @classmethod
    def refresh_import_lock(cls, connection: redis.Redis, token: str, ttl_seconds: int) -> bool:
        """
        Prodlouží expiraci importního locku pouze tehdy, pokud ho stále vlastní zadaný token.

        :param connection: Redis spojení, přes které se lock obnovuje.
        :param token: Jedinečný token vlastníka locku.
        :param ttl_seconds: Nová doba expirace locku v sekundách.
        :return: ``True``, pokud byl lock úspěšně obnoven; jinak ``False``.
        """
        return bool(connection.eval(cls._REFRESH_LOCK_SCRIPT, 1, cls.IMPORT_DATA_LOCK_KEY, token, ttl_seconds))

    @classmethod
    def persist_import_lock(cls, connection: redis.Redis, token: str) -> bool:
        """
        Odstraní expiraci importního locku pouze tehdy, pokud ho stále vlastní zadaný token.

        :param connection: Redis spojení, přes které se lock upravuje.
        :param token: Jedinečný token vlastníka locku.
        :return: ``True``, pokud byla expirace odstraněna; jinak ``False``.
        """
        return bool(connection.eval(cls._PERSIST_LOCK_SCRIPT, 1, cls.IMPORT_DATA_LOCK_KEY, token))

    @classmethod
    def release_import_lock(cls, connection: redis.Redis, token: str) -> bool:
        """
        Uvolní importní lock pouze tehdy, pokud ho stále vlastní zadaný token.

        :param connection: Redis spojení, přes které se lock maže.
        :param token: Jedinečný token vlastníka locku.
        :return: ``True``, pokud byl lock odstraněn; jinak ``False``.
        """
        return bool(connection.eval(cls._RELEASE_LOCK_SCRIPT, 1, cls.IMPORT_DATA_LOCK_KEY, token))

    @classmethod
    def delete_if_value_matches(cls, connection: redis.Redis, key: str, expected_value: str) -> bool:
        """
        Smaže libovolný klíč pouze tehdy, pokud jeho aktuální hodnota odpovídá ``expected_value``.

        Chrání job-routing ukazatele (``import_data_current_job_{user}``,
        ``IMPORT_DATA_ACTIVE_JOB_KEY``) před tím, aby terminální úklid jedné úlohy smazal ukazatel
        již přepsaný nově nastartovanou úlohou.

        :param connection: Redis spojení, přes které se klíč maže.
        :param key: Klíč ke smazání.
        :param expected_value: Hodnota, kterou musí klíč stále mít, aby ke smazání došlo.
        :return: ``True``, pokud byl klíč smazán; jinak ``False``.
        """
        return bool(connection.eval(cls._RELEASE_LOCK_SCRIPT, 1, key, expected_value))

    @classmethod
    def claim_awaiting_import(
        cls, connection: redis.Redis, job_id: str, expected_phase: str, new_phase: str, ttl_seconds: int
    ) -> tuple:
        """
        Atomicky ověří fázi, platnost validace i vlastnictví locku importní úlohy a v jediném
        volání ji převede z ``expected_phase`` do ``new_phase``, přičemž obnoví TTL locku.
        Sloučení kontroly a zápisu do jednoho Lua skriptu zabraňuje tomu, aby dva souběžné
        požadavky na start téhož importu prošly kontrolou fáze oba a naplánovaly stejnou úlohu dvakrát.

        :param connection: Redis spojení, přes které se operace provádí.
        :param job_id: Identifikátor importní úlohy.
        :param expected_phase: Fáze, ve které se úloha musí nacházet, aby byla nárokována.
        :param new_phase: Fáze, do které se úloha při úspěchu převede.
        :param ttl_seconds: Nová doba expirace globálního locku v sekundách.
        :return: Dvojice ``(claimed, lock_token)``; ``claimed`` je ``True`` při úspěchu, ``lock_token``
            je vlastnící token nebo ``None``, pokud úloha nebyla nárokována.
        """
        claimed, token = connection.eval(
            cls._CLAIM_AWAITING_IMPORT_SCRIPT,
            4,
            f"import_data_phase_{job_id}",
            f"import_data_valid_{job_id}",
            f"import_data_lock_token_{job_id}",
            cls.IMPORT_DATA_LOCK_KEY,
            expected_phase,
            new_phase,
            ttl_seconds,
        )
        return bool(claimed), (token or None)

    @classmethod
    def cancel_awaiting_import(cls, connection: redis.Redis, job_id: str, job_user: str, status_message: str) -> bool:
        """Atomicky zruší dosud nespouštěný import, pokud stále vlastní jeho lock.

        :param connection: Redis spojení použité pro atomické spuštění Lua skriptu.
        :param job_id: Identifikátor rušené importní úlohy.
        :param job_user: Identifikátor vlastníka úlohy použitý pro nalezení uživatelského ukazatele.
        :param status_message: Překladový identifikátor stavu uložený po úspěšném zrušení.
        :return: ``True``, pokud byla úloha zrušena; jinak ``False``.
        """
        return bool(
            connection.eval(
                cls._CANCEL_AWAITING_IMPORT_SCRIPT,
                6,
                f"import_data_phase_{job_id}",
                f"import_data_lock_token_{job_id}",
                cls.IMPORT_DATA_LOCK_KEY,
                f"import_data_status_message_tr_{job_id}",
                f"import_data_current_job_{job_user}",
                cls.IMPORT_DATA_ACTIVE_JOB_KEY,
                "awaiting_approval",
                "canceled",
                status_message,
                job_id,
            )
        )

    @classmethod
    def finalize_validation(cls, connection: redis.Redis, job_id: str) -> bool:
        """Atomicky převede vlastníkem drženou validaci do čekání na schválení.

        :param connection: Redis spojení použité pro atomické spuštění Lua skriptu.
        :param job_id: Identifikátor finalizované importní úlohy.
        :return: ``True``, pokud úloha stále vlastní lock a přechod proběhl; jinak ``False``.
        """
        return bool(
            connection.eval(
                cls._FINALIZE_VALIDATION_SCRIPT,
                4,
                f"import_data_phase_{job_id}",
                f"import_data_stop_{job_id}",
                f"import_data_lock_token_{job_id}",
                cls.IMPORT_DATA_LOCK_KEY,
                "validating",
                "awaiting_approval",
            )
        )

    @staticmethod
    def prepare_model_for_redis(table):
        """
        Převede řádek Django-tables2 tabulky do slovníku pro uložení do Redis cache.

        :param table: Tabulka (django-tables2) obsahující jeden řádek s daty záznamu.

            :return: Vrací proměnná ``data``.
        """
        columns = table.columns.iterall()
        row = table.rows[0]
        data = {}
        for column in columns:
            if getattr(column.column, "exclude_from_export", False):
                continue
            value = row.get_cell_value(column.name)
            if value and "nahled" not in column.name:
                data[column.name] = force_str(value)
            else:
                data[column.name] = ""
        return data


class ClamdError(Exception):
    """Základní třída výjimek pro chyby clamd."""

    pass


class ClamdResponseError(ClamdError):
    """Výjimka vyvolaná při neočekávané odpovědi od clamd."""

    pass


class ClamdBufferTooLongError(ClamdResponseError):
    """Výjimka vyvolaná při překročení délky bufferu nad StreamMaxLength v clamd.conf."""

    pass


class ClamdConnectionError(ClamdError):
    """Výjimka vyvolaná při chybách komunikace s clamd."""

    pass


class ClamdNetworkSocket:
    """
    Třída pro komunikaci s ClamAV démonem přes síťový socket.

    Tato třída poskytuje metody pro skenování souborů na viry
    pomocí ClamAV démona naslouchajícího na TCP portu.
    """

    def __init__(self):
        """
        Inicializace třídy.

        Hodnoty host, port a timeout se načítají z nastavení aplikace.
        """
        self.host = settings.CLAMD_HOST
        self.port = settings.CLAMD_PORT
        self.timeout = settings.CLAMD_TIMEOUT

    def instream(self, buff: BytesIO):
        """
        Skenuje buffer na přítomnost virů.

        :param buff: Binární stream (``BytesIO``) se souborem určeným ke kontrole.
        :return: Slovník ve formátu ``{filename: (status, reason)}`` pro odpověď clamd.
        :raises ClamdBufferTooLongError: Pokud je stream větší než povolený limit clamd.
        :raises ClamdConnectionError: Při chybě komunikace se službou clamd.
        """
        try:
            self._init_socket()
            self._send_command("INSTREAM")

            max_chunk_size = 1024

            chunk = buff.read(max_chunk_size)
            while chunk:
                size = struct.pack(b"!L", len(chunk))
                self.clamd_socket.send(size + chunk)
                chunk = buff.read(max_chunk_size)

            self.clamd_socket.send(struct.pack(b"!L", 0))

            result = self._recv_response()

            if len(result) > 0:
                if result == "INSTREAM size limit exceeded. ERROR":
                    raise ClamdBufferTooLongError(result)

                filename, reason, status = self._parse_response(result)
                return {filename: (status, reason)}
        finally:
            self._close_socket()

    def _basic_command(self, command):
        """
        Odešle jednoduchý příkaz do clamd a vrátí jeho odpověď.

        :param command: Název příkazu zasílaného do clamd démona (např. 'PING', 'VERSION').

        :return: Výstup funkce odpovídající implementované logice.

        :raises ClamdResponseError: Vyvolá se při splnění podmínky ``len(response) > 1``.
        """
        self._init_socket()
        try:
            self._send_command(command)
            response = self._recv_response().rsplit("ERROR", 1)
            if len(response) > 1:
                raise ClamdResponseError(response[0])
            else:
                return response[0]
        finally:
            self._close_socket()

    def _init_socket(self):
        """
        Inicializuje socketové připojení k clamd.

        Pouze pro interní použití.
        :raises ClamdConnectionError: Pokud se nelze připojit ke clamd.
        """
        try:
            self.clamd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clamd_socket.connect((self.host, self.port))
            self.clamd_socket.settimeout(self.timeout)
        except socket.error:
            e = sys.exc_info()[1]
            raise ClamdConnectionError(self._error_message(e))

    def _error_message(self, exception):
        """
        Formátuje chybovou zprávu pro selhání socketového připojení.
        :param exception: Zachycená síťová výjimka při navazování spojení.
        :return: Formátovaná chybová zpráva pro logování.
        """
        # argumenty pro socket.error mohou být buď (errno, "message")
        # nebo jen "message"
        if len(exception.args) == 1:
            return "Error connecting to {host}:{port}. {msg}.".format(
                host=self.host, port=self.port, msg=exception.args[0]
            )
        else:
            return "Error {erno} connecting {host}:{port}. {msg}.".format(
                erno=exception.args[0], host=self.host, port=self.port, msg=exception.args[1]
            )

    def _send_command(self, cmd, *args):
        """
               Odešle command.

               Používá prefix 'n' a ukončovač nového řádku podle doporučení `man clamd`.

               :param cmd: Textový název, klíč nebo zpráva ``cmd`` používaná v rámci operace.
               :param args: Parametr ``args`` se předává do volání ``join()``, ovlivňuje větvení podmínek.
        :return: Výstup funkce odpovídající implementované logice.
        """
        concat_args = ""
        if args:
            concat_args = " " + " ".join(args)

        cmd = "n{cmd}{args}\n".format(cmd=cmd, args=concat_args).encode("utf-8")
        self.clamd_socket.send(cmd)

    def _recv_response(self):
        """
        Přijme jednořádkovou odpověď od clamd.
        :return: Dekódovaný řádek odpovědi od clamd.
        :raises ClamdConnectionError: Při chybě čtení ze socketu.
        """
        try:
            with contextlib.closing(self.clamd_socket.makefile("rb")) as f:
                return f.readline().decode("utf-8").strip()
        except (socket.error, socket.timeout):
            e = sys.exc_info()[1]
            raise ClamdConnectionError("Error while reading from socket: {0}".format(e.args))

    def _parse_response(self, msg):
        """
        Parsuje odpovědi pro příkazy SCAN, CONTSCAN, MULTISCAN a STREAM.
        :param msg: Textová odpověď vrácená službou clamd.
        :return: N-tice ``(path, virus, status)`` extrahovaná z odpovědi.
        :raises ClamdResponseError: Pokud odpověď nelze naparsovat.
        """
        try:
            return scan_response.match(msg).group("path", "virus", "status")
        except AttributeError:
            raise ClamdResponseError(msg.rsplit("ERROR", 1)[0])

    def _close_socket(self):
        """Uzavře socketové připojení k clamd."""
        self.clamd_socket.close()
        return
