from polib import pofile
from pathlib import Path
import os


def find_v2(po_file, st, by="msgid", include_obsolete_entries=False, msgctxt=False):
    """
    Find the entry which msgid (or property identified by the ``by``
    argument) matches the string ``st``.

    Keyword arguments:

    ``st``
        string, the string to search for.

    ``by``
        string, the property to use for comparison (default: ``msgid``).

    ``include_obsolete_entries``
        boolean, whether to also search in entries that are obsolete.

    ``msgctxt``
        string, allows specifying a specific message context for the
        search.
    """
    if include_obsolete_entries:
        entries = po_file[:]
    else:
        entries = [e for e in po_file if not e.obsolete]
    matches = []
    for e in entries:
        if by == "occurrences":
            if st[0] in e.occurrences:
                if msgctxt is not False and e.msgctxt != msgctxt:
                    continue
                matches.append(e)
        elif getattr(e, by) == st:
            if msgctxt is not False and e.msgctxt != msgctxt:
                continue
            matches.append(e)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        if not msgctxt:
            # find the entry with no msgctx
            e = None
            for m in matches:
                if not m.msgctxt:
                    e = m
            if e:
                return e
            # fallback to the first entry found
            return matches[0]
    return None


BASE_DIR = Path(__file__).resolve()
print(BASE_DIR.parent.parent)

path_new = os.path.join(BASE_DIR.parent.parent, "preklady/new_django.po.cs/django.po")
path_old = os.path.join(
    BASE_DIR.parent.parent, "preklady/django.po.cs_backup/django.po"
)
print(path_new)
po_file_new = pofile(path_new)
po_file_old = pofile(path_old)
for entry_new in po_file_new:
    entry_old = find_v2(po_file_old, entry_new.occurrences, "occurrences")
    if entry_old:
        if entry_old.msgstr:
            entry_new.msgstr = entry_old.msgstr
        else:
            entry_new.msgstr = entry_old.msgid
    else:
        print(entry_new.occurrences)
po_file_new.save()
