import os
from pathlib import Path

from polib import pofile


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
            if len(st) > 0 and st[0] in e.occurrences:
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
path_new = os.path.join(BASE_DIR.parent.parent, "preklady/new_django.po.cs/django.po")
path_old = os.path.join(BASE_DIR.parent.parent, "preklady/django.po.cs_backup/django_oznameni.po")
po_file_new = pofile(path_new)
po_file_old = pofile(path_old)
rewrite_only = "oznameni/"
print("Not found entries:")
for entry_new in po_file_new:
    if len(entry_new.occurrences) > 0 and rewrite_only in entry_new.occurrences[0][0]:
        entry_old_msgid = find_v2(po_file_old, entry_new.msgid)
        if not entry_old_msgid:
            entry_old = find_v2(po_file_old, entry_new.occurrences, "occurrences")
            if entry_old:
                if entry_old.msgstr:
                    entry_new.msgstr = entry_old.msgstr
                else:
                    entry_new.msgstr = entry_old.msgid
            else:
                print(f"entry: {entry_new.msgid}, occurences: {entry_new.occurrences}")
        else:
            entry_new.msgstr = entry_old_msgid.msgstr
        entry_new.flags.append("fuzzy")
po_file_new.save()
