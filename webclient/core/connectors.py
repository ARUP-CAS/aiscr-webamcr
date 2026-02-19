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
    r = None
    r_decode = None

    @classmethod
    def _create_connection(cls):
        cls.r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=get_plain_redis_pass())

    # tento connector vrací přímo string, takže není potřeba volat value.decode("utf-8")
    @classmethod
    def _create_connection_decode(cls):
        cls.r_decode = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=get_plain_redis_pass(), decode_responses=True
        )

    @classmethod
    def get_connection(cls) -> redis.Redis:
        if not cls.r:
            cls._create_connection()
        return cls.r

    @classmethod
    def get_connection_decode(cls) -> redis.Redis:
        if not cls.r_decode:
            cls._create_connection_decode()
        return cls.r_decode

    @staticmethod
    def prepare_model_for_redis(table):
        columns = table.columns.iterall()
        row = table.rows[0]
        data = {}
        for column in columns:
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

        Args:
            buff: instance BytesIO se soubory ke skenování

        Returns:
            dict: {filename: (status, reason)} kde status je 'FOUND' nebo 'OK'

        Raises:
            ClamdBufferTooLongError: pokud velikost bufferu překročí limity clamd
            ClamdConnectionError: při problému s komunikací
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
        Odešle příkaz na clamav server a vrátí odpověď.

        Args:
            command (str): příkaz k odeslání

        Returns:
            str: odpověď od clamd

        Raises:
            ClamdConnectionError: při problému s komunikací
            ClamdResponseError: pokud clamd vrátí chybu
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

        Raises:
            ClamdConnectionError: pokud se nelze připojit k clamd
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

        Args:
            exception: výjimka socket.error

        Returns:
            str: formátovaná chybová zpráva
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
        Odešle příkaz do clamd.

        Používá prefix 'n' a ukončovač nového řádku podle doporučení `man clamd`.

        Args:
            cmd (str): příkaz k odeslání
            *args: dodatečné argumenty pro příkaz
        """
        concat_args = ""
        if args:
            concat_args = " " + " ".join(args)

        cmd = "n{cmd}{args}\n".format(cmd=cmd, args=concat_args).encode("utf-8")
        self.clamd_socket.send(cmd)

    def _recv_response(self):
        """
        Přijme jednořádkovou odpověď od clamd.

        Returns:
            str: dekódovaný a oříznutý řádek odpovědi

        Raises:
            ClamdConnectionError: při chybě čtení ze socketu
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

        Args:
            msg (str): zpráva odpovědi od clamd

        Returns:
            tuple: (path, virus, status)

        Raises:
            ClamdResponseError: pokud nelze odpověď parsovat
        """
        try:
            return scan_response.match(msg).group("path", "virus", "status")
        except AttributeError:
            raise ClamdResponseError(msg.rsplit("ERROR", 1)[0])

    def _close_socket(self):
        """
        Uzavře socketové připojení k clamd.
        """
        self.clamd_socket.close()
        return
