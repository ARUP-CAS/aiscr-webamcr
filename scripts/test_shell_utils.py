"""Společné nalezení Bashe pro izolované shellové regrese."""

import os
import shutil
from pathlib import Path


def bash_executable():
    """Najde Git Bash vůči instalaci Gitu, jinak použije Bash z PATH.

    :return: Cesta k interpretu nebo ``None``; spouštěč WSL není Bash pro tyto testy.
    """
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            candidate = Path(git).resolve().parents[1] / "bin/bash.exe"
            if candidate.is_file():
                return str(candidate)
    fallback = shutil.which("bash")
    if fallback and os.name == "nt":
        normalized = fallback.replace("\\", "/").lower()
        if normalized.endswith(("/windows/system32/bash.exe", "/windows/sysnative/bash.exe")):
            return None
    return fallback
