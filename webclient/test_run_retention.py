"""Udržuje omezenou historii pokusů s uzamčeným vlastnictvím a bezpečnými hranicemi."""

import errno
import os
import shutil
import stat
import tempfile
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path

from test_run_results import attempt_identity, read_outcome, validate_identity, validate_record

LOCK_MARKER = b"AMCR test attempt lease v1\n"
STALE_SECONDS = 30 * 24 * 60 * 60


def linked(path):
    """Rozpozná odkazy i Windows junction.

    :param path: Kontrolovaná cesta.
    :return: Zda cesta překračuje běžný adresář či soubor.
    """
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def layout(root):
    """Připraví pouze vlastní adresáře a odmítne přesměrované hranice.

    :param root: Nakonfigurovaný kořen výsledků.
    :return: Kořen pokusů a adresář jejich zámků.
    """
    root = Path(root).resolve()
    runs = root / "runs"
    leases = runs / ".leases"
    for path in (runs, leases):
        if linked(path):
            raise ValueError("Přesměrovaný adresář retence")
        path.mkdir(parents=True, exist_ok=True)
        if path.resolve() != path or not path.is_dir():
            raise ValueError("Neplatná hranice retence")
    return runs, leases


class FileLease:
    """Drží OS zámek souboru napříč procesy i kontejnery stejného hostitele."""

    def __init__(self, path, create=False):
        """Otevře ověřený soubor; neznámý existující obsah nepřepíše.

        :param path: Soubor zámku v ověřeném adresáři.
        :param create: Povolit založení vlastního zámku.
        """
        self.path, self.stream, self.locked = path, None, False
        if linked(path):
            raise ValueError("Odkaz místo zámku")
        try:
            existing = path.lstat()
        except FileNotFoundError:
            pass
        else:
            if not stat.S_ISREG(existing.st_mode):
                raise ValueError("Neplatný soubor zámku")
        flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags | (os.O_CREAT | os.O_EXCL if create else 0), 0o600)
            fresh = create
        except FileExistsError:
            fd = os.open(path, flags)
            fresh = False
        self.stream = os.fdopen(fd, "r+b", buffering=0)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode) or not os.path.samestat(
                os.fstat(fd), path.stat(follow_symlinks=False)
            ):
                raise ValueError("Neplatný soubor zámku")
            if fresh:
                self.stream.write(LOCK_MARKER)
                os.fsync(fd)
        except BaseException:
            self.stream.close()
            raise

    def acquire(self, blocking=True):
        """Získá zámek a teprve poté ověří označení vlastnictví.

        :param blocking: Čekat na zámek.
        :return: Zda byl zámek získán.
        """
        try:
            self.stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.stream.fileno(), msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            self.locked = True
        except OSError as exc:
            if not blocking and (
                exc.errno in (errno.EACCES, errno.EAGAIN) or getattr(exc, "winerror", None) in (32, 33)
            ):
                return False
            raise
        self.stream.seek(0)
        if self.stream.read(len(LOCK_MARKER) + 1) != LOCK_MARKER:
            raise ValueError("Neznámé vlastnictví zámku")
        return True

    def close(self):
        """Uvolní pouze vlastní OS zámek a deskriptor."""
        if self.stream is None or self.stream.closed:
            return
        try:
            if self.locked:
                self.stream.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        finally:
            self.stream.close()


def publish_root_marker(path):
    """Zveřejní úplný marker bez nahrazení souběžně vytvořeného zámku.

    :param path: Cesta kořenového zámku v ověřeném adresáři.
    """
    stream = tempfile.NamedTemporaryFile(dir=path.parent, prefix=".retention-", delete=False)
    temporary = Path(stream.name)
    try:
        with stream:
            stream.write(LOCK_MARKER)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            # Windows rename fails if the target exists. On POSIX use a hard
            # link to publish without replacing the winner.
            if os.name == "nt":
                temporary.rename(path)
            else:
                os.link(temporary, path)
        except FileExistsError:
            pass
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked_root(runs):
    """Serializuje vytváření a prořezávání pokusů.

    :param runs: Ověřený kořen pokusů.
    :yield: Žádná hodnota; zámek platí uvnitř kontextu.
    """
    path = runs / ".retention.lock"
    try:
        lease = FileLease(path)
    except FileNotFoundError:
        publish_root_marker(path)
        lease = FileLease(path)
    try:
        lease.acquire()
        yield
    finally:
        lease.close()


def terminal_record(directory):
    """Rozpozná vlastněný terminální záznam bez přijetí jeho počtů jako výsledku.

    :param directory: Přímý adresář pokusu.
    :return: Záznam nebo None, pokud ještě není publikován.
    """
    try:
        record = read_outcome(directory)
    except FileNotFoundError:
        return None
    return validate_record(record, directory.name, record["mode"], record["number"], allow_legacy=True)


def contained_activity(directory, runs):
    """Ověří celý kandidát a zjistí poslední aktivitu bez následování odkazů.

    :param directory: Kandidát retence.
    :param runs: Ověřený kořen.
    :return: Poslední čas aktivity.
    """
    if linked(directory) or directory.resolve().parent != runs:
        raise ValueError("Kandidát překračuje hranici retence")
    latest = directory.stat().st_mtime
    for parent, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            if linked(path) or not path.resolve().is_relative_to(directory):
                raise ValueError("Odkaz uvnitř kandidáta retence")
            latest = max(latest, path.stat().st_mtime)
    return latest


def prune_locked(runs, leases, current=None, now=None):
    """Prořeže jen ověřené neaktivní kandidáty během kořenového zámku.

    :param runs: Kořen pokusů.
    :param leases: Kořen zámků.
    :param current: Vždy chráněná identita aktuálního pokusu.
    :param now: Volitelný čas pro přesné testy hranic.
    :return: Seznam odstraněných identit.
    """
    now = time.time() if now is None else now
    finished, stale, removed = [], [], []
    with ExitStack() as held:
        for directory in sorted(runs.iterdir()):
            if directory.name.startswith(".") or not directory.is_dir():
                continue
            try:
                validate_identity(directory.name)
                activity = contained_activity(directory, runs)
                record = terminal_record(directory)
            except (OSError, ValueError, KeyError, TypeError):
                print("Retence: neověřený kandidát zachován", flush=True)
                continue
            protected = directory.name == current
            lock_path = leases / (directory.name + ".lock")
            if not protected:
                try:
                    lease = FileLease(lock_path, create=record is not None and record["version"] == 1)
                    held.callback(lease.close)
                    protected = not lease.acquire(blocking=False)
                except (FileNotFoundError, ValueError):
                    print("Retence: neověřené vlastnictví zachováno", flush=True)
                    continue
            if record is not None:
                finished.append(((directory / "outcome.json").stat().st_mtime, directory.name, directory, protected))
            elif not protected and now - activity >= STALE_SECONDS:
                stale.append(directory)
        keep = {item[1] for item in sorted(finished, reverse=True)[:10]}
        candidates = stale + [item[2] for item in finished if not item[3] and item[1] not in keep]
        for directory in candidates:
            contained_activity(directory, runs)
            # Recheck the literal direct-child boundary immediately before recursive removal.
            if directory.parent != runs or directory.resolve().parent != runs or linked(directory):
                raise ValueError("Změněná hranice retence")
            shutil.rmtree(directory)
            removed.append(directory.name)
    for identity in removed:
        path = leases / (identity + ".lock")
        if linked(path):
            raise ValueError("Změněný zámek retence")
        path.unlink(missing_ok=True)
    return removed


def prune_attempts(root, current=None, now=None):
    """Spustí bezpečný úklid včetně serializace.

    :param root: Kořen výsledků.
    :param current: Chráněná identita.
    :param now: Testovací čas.
    :return: Odstraněné identity.
    """
    runs, leases = layout(root)
    with locked_root(runs):
        return prune_locked(runs, leases, current, now)


class AttemptLease:
    """Drží živé vlastnictví od vytvoření až po závěrečnou retenci pokusu."""

    def __init__(self, root, identity, creator):
        """Odmítne kolizi a před vytvořením adresáře uzamkne vlastnictví pokusu.

        :param root: Kořen výsledků.
        :param identity: Požadovaná identita nebo None.
        :param creator: Produkční funkce pro založení adresáře.
        """
        self.root = root
        self.identity = attempt_identity(identity)
        runs, leases = layout(root)
        with locked_root(runs):
            try:
                (runs / self.identity).lstat()
            except FileNotFoundError:
                pass
            else:
                raise FileExistsError("Identita pokusu již existuje")
            prune_locked(runs, leases)
            self.lease = FileLease(leases / (self.identity + ".lock"), create=True)
            try:
                # A valid unclaimed marker can remain after interruption before mkdir.
                if not self.lease.acquire(blocking=False):
                    raise ValueError("Identitu pokusu již vlastní jiný proces")
                self.directory, _ = creator(root, self.identity)
            except BaseException:
                self.lease.close()
                raise

    def close(self):
        """Uplatní závěrečnou retenci, přitom stále chrání aktuální pokus."""
        try:
            prune_attempts(self.root, current=self.identity)
        finally:
            self.lease.close()
