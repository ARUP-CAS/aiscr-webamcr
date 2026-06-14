"""Sdílená in-memory náhrada za Redis pro účely jednotkových testů."""


class FakeRedis:
    """Minimální in-memory náhrada za ``redis.Redis`` použitelná v unit testech.

    Podporuje pouze operace, které využívá importní pipeline (``cron.tasks.run_data_import``)
    a další taskové cesty: ``get``/``set``/``delete``/``expire``/``rpush``/``lrange``/``lset``
    a no-op ``eval``. Pokud bude test potřebovat další metody, doplňte je sem.
    """

    def __init__(self, initial: dict | None = None):
        """
        Inicializuje prázdné úložiště a volitelně předvyplní hodnoty.

        :param initial: Volitelný slovník výchozích klíčů a hodnot, který se ihned uloží přes ``set``.
        """
        self._kv: dict[str, bytes] = {}
        self._lists: dict[str, list[bytes]] = {}
        for key, value in (initial or {}).items():
            self.set(key, value)

    @staticmethod
    def _encode(value) -> bytes:
        """Zakóduje vstup na ``bytes`` stejně, jako by to udělal reálný Redis klient bez ``decode_responses``."""
        if isinstance(value, bytes):
            return value
        return str(value).encode("utf-8")

    def set(self, key, value, ex=None, nx=False):
        """
        Uloží hodnotu pod klíč; ``nx=True`` zapíše pouze pokud klíč neexistuje.

        :param key: Klíč v úložišti.
        :param value: Hodnota k uložení (kóduje se na ``bytes``).
        :param ex: Ignorováno — FakeRedis neimplementuje TTL.
        :param nx: Pokud ``True`` a klíč existuje, nic se nezapíše a vrátí se ``False``.
        :return: ``True`` při zápisu, ``False`` pokud byl ``nx=True`` a klíč již existoval.
        """
        encoded = self._encode(value)
        if nx and key in self._kv:
            return False
        self._kv[key] = encoded
        return True

    def get(self, key):
        """Vrátí ``bytes`` hodnotu nebo ``None``, pokud klíč není uložen.

        :param key: Redis klíč čtené hodnoty.
        """
        return self._kv.get(key)

    def delete(self, *keys):
        """Smaže předané klíče (i listy) a vrátí počet skutečně odstraněných položek.

        :param keys: Redis klíče určené ke smazání.
        """
        removed = 0
        for key in keys:
            removed += int(self._kv.pop(key, None) is not None)
            removed += int(self._lists.pop(key, None) is not None)
        return removed

    def expire(self, key, seconds):
        """No-op: FakeRedis nesleduje TTL; vrací ``True``, pokud klíč existuje.

        :param key: Redis klíč, pro který se nastavuje TTL.
        :param seconds: Počet sekund TTL ignorovaný fake implementací.
        """
        return key in self._kv or key in self._lists

    def rpush(self, key, value):
        """Přidá hodnotu na konec listu pod klíčem a vrátí novou délku listu.

        :param key: Redis klíč seznamu.
        :param value: Hodnota přidaná na konec seznamu.
        """
        self._lists.setdefault(key, []).append(self._encode(value))
        return len(self._lists[key])

    def lrange(self, key, start, stop):
        """Vrátí výřez listu kompatibilní s Redis sémantikou (``stop=-1`` znamená do konce).

        :param key: Redis klíč seznamu.
        :param start: Počáteční index výřezu.
        :param stop: Koncový index výřezu.
        """
        items = self._lists.get(key, [])
        if stop == -1:
            return list(items[start:])
        return list(items[start : stop + 1])

    def lset(self, key, index, value):
        """Nastaví hodnotu v listu na zadaném indexu.

        :param key: Redis klíč seznamu.
        :param index: Index položky, která se má přepsat.
        :param value: Nová hodnota položky.
        """
        self._lists[key][index] = self._encode(value)

    def eval(self, *args, **kwargs):
        """No-op pro Redis Lua skripty — vrací 1, aby refresh/release lock vždy uspěl.

        :param args: Poziční argumenty volání Redis ``eval``.
        :param kwargs: Pojmenované argumenty volání Redis ``eval``.
        """
        return 1
