import glob
import os
from pathlib import Path

files = glob.glob(str(Path(__file__).resolve().parent.parent / "webclient/*/migrations/*.py"))
for f in files:
    try:
        if not str(f).endswith("__init__.py"):
            os.remove(f)
            print("Removing migration file ... " + str(f))
    except OSError as e:
        print("Error: %s : %s" % (f, e.strerror))
