"""Blokování síťových volání Pythonu před importem aplikace v CI."""

import os
import socket
import sys


class ForbiddenNetworkRequest(RuntimeError):
    """Odmítne volání bez HTTP retry, ale umožní unittest uklidit a dokončit sadu."""


def allowed_address(address):
    """Povolí pouze lokální porty služeb CI, případně unixový socket.

    :param address: Cílový tuple host/port nebo cesta unixového socketu.
    :return: Zda je cíl lokální službou povolenou v CI.
    """
    if isinstance(address, (str, bytes)):
        return True  # AF_UNIX; IP adresy mají tvar tuple.
    return (
        isinstance(address, tuple)
        and len(address) >= 2
        and address[0] in {"127.0.0.1", "::1", "localhost"}
        and address[1]
        in {int(os.environ.get("AMCR_CI_DB_PORT", "5432")), int(os.environ.get("AMCR_CI_REDIS_PORT", "6379"))}
    )


def install():
    """Nainstaluje audit hook; odmítnutí zaznamená i při zachycení výjimky testem."""

    def audit(event, args):
        """Odmítne vzdálené DNS, TCP a UDP před skutečným síťovým voláním."""
        denied = False
        if event in {"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr"}:
            denied = args[0] not in {None, "localhost", "127.0.0.1", "::1"}
        elif event in {"socket.connect", "socket.sendto"}:
            sock, address = args[0], args[-1]
            denied = sock.family in {socket.AF_INET, socket.AF_INET6} and not allowed_address(address)
        if denied:
            target = args[0] if event.startswith("socket.get") else args[-1]
            message = f"CI network access blocked: {event} {target!r}"
            log = os.environ.get("AMCR_CI_NETWORK_LOG")
            if log:
                with open(log, "a", encoding="utf-8") as stream:
                    stream.write(message + "\n")
            raise ForbiddenNetworkRequest(message)

    sys.addaudithook(audit)
