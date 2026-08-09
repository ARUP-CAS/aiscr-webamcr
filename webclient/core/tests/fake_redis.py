"""Sdílená in-memory náhrada za Redis pro účely jednotkových testů."""

import fnmatch


class FakeRedis:
    """Minimální in-memory náhrada za ``redis.Redis`` použitelná v unit testech.

    Podporuje operace, které využívá importní pipeline (``cron.tasks.run_data_import`` i
    ``cron.tasks.run_data_import_validation``) a další taskové cesty:
    ``get``/``set``/``delete``/``expire``/``persist``/``rpush``/``lrange``/``lset``/``incr``/
    ``scan_iter`` a konfigurabilní ``eval``. ``pipeline()`` vrací ``FakePipeline``, který operace zaznamená
    a při ``execute()`` je sekvenčně provede nad stejným úložištěm; podporuje ``get``/``set``/
    ``delete``/``expire``/``persist``/``rpush``/``incr``. Pokud bude test potřebovat další
    metody, doplňte je sem.
    """

    def __init__(self, initial: dict | None = None, eval_results: list | None = None, decode_responses: bool = False):
        """
        Inicializuje prázdné úložiště a volitelně předvyplní hodnoty.

        :param initial: Volitelný slovník výchozích klíčů a hodnot, který se ihned uloží přes ``set``.
        :param eval_results: Volitelný seznam návratových hodnot pro postupné volání ``eval()``.
            Každé volání ``eval()`` odebere první položku seznamu. Po vyčerpání seznamu vrátí vždy ``1``.
            ``None`` (výchozí) znamená vždy vrátit ``1`` bez omezení.
        :param decode_responses: Pokud ``True``, čtecí operace (``get``, ``lrange`` a pipeline ``get``)
            vracejí ``str`` místo ``bytes`` — emuluje klienta z ``get_connection_decode()``, který
            používají view (``DataImportProgress``, ``DataImportStop``, ``DataImportCancel`` …).
            Výchozí ``False`` zachovává bytovou sémantiku ``get_connection()`` pro taskové testy.
        """
        self._kv: dict[str, bytes] = {}
        self._lists: dict[str, list[bytes]] = {}
        self._eval_results: list = list(eval_results) if eval_results is not None else []
        self._decode = decode_responses
        for key, value in (initial or {}).items():
            self.set(key, value)

    @staticmethod
    def _encode(value) -> bytes:
        """Zakóduje vstup na ``bytes`` stejně, jako by to udělal reálný Redis klient bez ``decode_responses``."""
        if isinstance(value, bytes):
            return value
        return str(value).encode("utf-8")

    def _maybe_decode(self, value):
        """Dekóduje ``bytes`` na ``str``, pokud fake emuluje klienta s ``decode_responses=True``.

        :param value: Hodnota načtená z úložiště (``bytes`` nebo ``None``).
        :return: ``str`` v decode režimu, jinak původní hodnota beze změny.
        """
        if self._decode and isinstance(value, bytes):
            return value.decode("utf-8")
        return value

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
        return self._maybe_decode(self._kv.get(key))

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

    def persist(self, key):
        """No-op symetrický k ``expire``: vrací ``True``, pokud klíč existuje (TTL se neřeší).

        :param key: Redis klíč, u kterého se má zrušit expirace.
        """
        return key in self._kv or key in self._lists

    def scan_iter(self, match=None):
        """Projde klíče úložiště odpovídající glob vzoru (zjednodušený ``SCAN``).

        Reálný Redis nezaručuje pořadí ani unikátnost napříč iteracemi; fake vrací klíče
        v pořadí vložení, což pro testy stačí.

        :param match: Glob vzor (např. ``import_data_ABC_record_*``); ``None`` vrátí vše.
        :return: Generátor klíčů odpovídajících vzoru.
        """
        for key in list(self._kv.keys()) + list(self._lists.keys()):
            if match is None or fnmatch.fnmatchcase(key, match):
                yield key

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
        sliced = items[start:] if stop == -1 else items[start : stop + 1]
        return [self._maybe_decode(item) for item in sliced]

    def lset(self, key, index, value):
        """Nastaví hodnotu v listu na zadaném indexu.

        :param key: Redis klíč seznamu.
        :param index: Index položky, která se má přepsat.
        :param value: Nová hodnota položky.
        """
        self._lists[key][index] = self._encode(value)

    def incr(self, key, amount=1):
        """Inkrementuje celočíselnou hodnotu pod klíčem a vrátí novou hodnotu.

        :param key: Redis klíč číselného čítače.
        :param amount: O kolik se hodnota zvýší (výchozí ``1``).
        :return: Nová hodnota čítače po inkrementu.
        """
        current = int(self._kv.get(key, b"0")) if key in self._kv else 0
        current += amount
        self._kv[key] = str(current).encode("utf-8")
        return current

    def pipeline(self):
        """Vrátí ``FakePipeline`` sdílející toto úložiště; operace se provedou až při ``execute()``.

        :return: Instance ``FakeRedis.FakePipeline`` nad tímto úložištěm.
        """
        return FakeRedis.FakePipeline(self)

    def eval(self, script, numkeys, *keys_and_args):
        """Simuluje Redis Lua skript — vrací hodnotu z ``eval_results``, jinak reálně vykoná
        compare-then-delete (``RedisConnector._RELEASE_LOCK_SCRIPT``/``delete_if_value_matches``)
        nebo compare-then-transition (``RedisConnector._CLAIM_AWAITING_IMPORT_SCRIPT``).

        Pokud byl při inicializaci předán ``eval_results``, odebere a vrátí první položku seznamu
        (beze změny úložiště) — pro testy, které chtějí vynutit konkrétní výsledek locku. Jinak,
        pro compare-then-delete skript klíč skutečně smaže, pokud jeho hodnota odpovídá
        očekávané; pro claim skript ověří fázi/validitu/token a fázi skutečně přepne
        (bez toho nešel otestovat souběh dvou Start požadavků);
        jiné skripty (refresh/persist) vrací ``1`` beze změny úložiště.

        :param script: Zdrojový text Lua skriptu (rozlišuje se dle přítomnosti ``\"del\"``
            resp. ``\"return {1, token}\"``).
        :param numkeys: Počet KEYS argumentů na začátku ``keys_and_args``.
        :param keys_and_args: KEYS následované ARGV, stejně jako u reálného Redis ``eval``.
        :return: První zbývající hodnota z ``eval_results``, nebo výsledek simulace.
        """
        if self._eval_results:
            return self._eval_results.pop(0)
        keys = keys_and_args[:numkeys]
        argv = keys_and_args[numkeys:]
        if "return {1, token}" in script:
            return self._eval_claim_awaiting_import(keys, argv)
        if "del" in script and keys and argv:
            key = keys[0]
            if self._kv.get(key) == self._encode(argv[0]):
                self.delete(key)
                return 1
            return 0
        return 1

    def _eval_claim_awaiting_import(self, keys, argv):
        """Vykoná simulaci ``RedisConnector._CLAIM_AWAITING_IMPORT_SCRIPT``.

        Ověří fázi, validitu a vlastnictví locku úlohy a při shodě atomicky přepne fázi na
        ``new_phase`` — stejně jako reálný Lua skript, ale nad in-memory úložištěm.

        :param keys: ``(phase_key, valid_key, lock_token_key, global_lock_key)`` z ``KEYS``.
        :param argv: ``(expected_phase, new_phase, ttl_seconds)`` z ``ARGV``.
        :return: ``[1, token]`` při úspěšném nároku, jinak ``[0, ""]``.
        """
        phase_key, valid_key, lock_token_key, global_lock_key = keys
        expected_phase, new_phase, _ttl_seconds = argv
        if self._kv.get(phase_key) != self._encode(expected_phase):
            return [0, ""]
        if self._kv.get(valid_key) != self._encode("1"):
            return [0, ""]
        token_raw = self._kv.get(lock_token_key)
        if token_raw is None or self._kv.get(global_lock_key) != token_raw:
            return [0, ""]
        self.set(phase_key, new_phase)
        return [1, self._maybe_decode(token_raw)]

    class FakePipeline:
        """Record-then-execute pipeline nad ``FakeRedis`` — operace se provedou až při ``execute()``."""

        def __init__(self, redis: "FakeRedis"):
            """Váže pipeline k danému úložišti a inicializuje prázdnou frontu operací.

            :param redis: Vlastník úložiště, nad kterým se operace provedou.
            """
            self._redis = redis
            self._ops: list = []

        def get(self, key):
            """Zaznamená ``get`` operaci do fronty.

            :param key: Redis klíč čtené hodnoty.
            """
            self._ops.append(("get", key))
            return self

        def set(self, key, value, ex=None, nx=False):
            """Zaznamená ``set`` operaci do fronty.

            :param key: Redis klíč zapisované hodnoty.
            :param value: Hodnota k uložení.
            :param ex: Ignorováno — FakeRedis neimplementuje TTL.
            :param nx: Pokud ``True``, zapiš pouze při neexistenci klíče.
            """
            self._ops.append(("set", key, value, ex, nx))
            return self

        def delete(self, *keys):
            """Zaznamená ``delete`` operaci do fronty.

            :param keys: Redis klíče určené ke smazání.
            """
            self._ops.append(("delete", keys))
            return self

        def expire(self, key, seconds):
            """Zaznamená ``expire`` operaci do fronty.

            :param key: Redis klíč, pro který se nastavuje TTL.
            :param seconds: Počet sekund TTL (fake implementací ignorováno).
            """
            self._ops.append(("expire", key, seconds))
            return self

        def persist(self, key):
            """Zaznamená ``persist`` operaci do fronty.

            :param key: Redis klíč, u kterého se má zrušit expirace.
            """
            self._ops.append(("persist", key))
            return self

        def rpush(self, key, value):
            """Zaznamená ``rpush`` operaci do fronty.

            :param key: Redis klíč seznamu.
            :param value: Hodnota přidaná na konec seznamu.
            """
            self._ops.append(("rpush", key, value))
            return self

        def incr(self, key, amount=1):
            """Zaznamená ``incr`` operaci do fronty.

            :param key: Redis klíč číselného čítače.
            :param amount: O kolik se hodnota zvýší.
            """
            self._ops.append(("incr", key, amount))
            return self

        def execute(self):
            """Provede zaznamenané operace sekvenčně a vrátí seznam jejich návratových hodnot.

            :return: Seznam návratových hodnot v pořadí zaznamenaných operací.
            """
            results = []
            for op in self._ops:
                name = op[0]
                if name == "get":
                    results.append(self._redis.get(op[1]))
                elif name == "set":
                    results.append(self._redis.set(op[1], op[2], ex=op[3], nx=op[4]))
                elif name == "delete":
                    results.append(self._redis.delete(*op[1]))
                elif name == "expire":
                    results.append(self._redis.expire(op[1], op[2]))
                elif name == "persist":
                    results.append(self._redis.persist(op[1]))
                elif name == "rpush":
                    results.append(self._redis.rpush(op[1], op[2]))
                elif name == "incr":
                    results.append(self._redis.incr(op[1], op[2]))
            self._ops = []
            return results
