from polib import pofile
from pathlib import Path


BASE_DIR = Path(__file__).resolve()
path_new = "/Users/janihnat/Downloads/django_v3.po"
path_old = "/Users/janihnat/Downloads/django_v2.po"
po_file_new = pofile(path_new)
po_file_old = pofile(path_old)
for e in po_file_old:
    if po_file_new[1].occurrences[3] in e.occurrences:
        print(po_file_new[1].occurrences[3])
        print(e.msgid)
for entry_new in po_file_new:
    entry_old = po_file_old.find(entry_new.occurrences, "occurrences")
    if entry_old:
        if entry_old.msgstr:
            entry_new.msgstr = entry_old.msgstr
        else:
            entry_new.msgstr = entry_old.msgid
po_file_new.save()
