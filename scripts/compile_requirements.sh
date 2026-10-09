#!/bin/bash
# Zkompiluje autorské soubory webclient/requirements*.in do requirements*.txt
# s úplnými tranzitivními piny (pip-tools).
#
# Kompilace běží v Linux kontejneru se stejnou verzí Pythonu jako produkční image,
# aby piny a markery odpovídaly prostředí, kde se balíčky instalují.
#
# Použití:
#   scripts/compile_requirements.sh                 # přegeneruje vše, zachová stávající piny
#   scripts/compile_requirements.sh -P Django       # aktualizuje jeden balíček
#   scripts/compile_requirements.sh --upgrade       # aktualizuje vše na nejnovější verze
#
# Další argumenty se předávají pip-compile.

set -euo pipefail

PYTHON_IMAGE="python:3.14-slim"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Verze pip-tools se bere z pinu v requirements-dev.txt (autorsky v requirements-dev.in),
# takže ji Dependabot aktualizuje na jednom místě i pro tento skript.
PIP_TOOLS_VERSION="$(tr -d '\r' < "${repo_root}/webclient/requirements-dev.txt" | sed -n 's/^pip-tools==//p')"
if [ -z "${PIP_TOOLS_VERSION}" ]; then
    echo "Chybí pin pip-tools== ve webclient/requirements-dev.txt" >&2
    exit 1
fi

# Dependabot tento skript nespouští: soubory kompiluje vlastním pip-compile a jeho přepínače
# (např. --strip-extras) odvozuje z textu hlavičky vygenerovaného .txt. Přepínače proto musí
# být vypsané v CUSTOM_COMPILE_COMMAND. Hlavička nesmí obsahovat --output-file ani názvy
# .in souborů, jinak by Dependabot špatně spároval .in a .txt.
PIP_COMPILE_FLAGS="--allow-unsafe --strip-extras --no-emit-index-url"

# Pořadí je důležité: test a docs zahrnují requirements.txt, dev zahrnuje requirements-test.txt.
# Vrstvy se propojují přes -r, ne přes -c: Dependabot řadí rekompilaci vrstev jen podle -r,
# s -c by vyšší vrstvu mohl zkompilovat dřív než základ a aktualizace sdíleného balíčku by selhala.
# Argumenty skriptu se escapují, aby přežily vložení do příkazu kontejneru.
extra_args=""
for arg in "$@"; do
    extra_args+=" $(printf '%q' "$arg")"
done

MSYS_NO_PATHCONV=1 docker run --rm \
    -v "${repo_root}/webclient:/webclient" \
    -w /webclient \
    -e CUSTOM_COMPILE_COMMAND="scripts/compile_requirements.sh (pip-compile ${PIP_COMPILE_FLAGS})" \
    "${PYTHON_IMAGE}" \
    bash -euo pipefail -c "
        pip install --quiet --root-user-action=ignore pip-tools==${PIP_TOOLS_VERSION}
        for name in requirements requirements-test requirements-dev requirements-docs; do
            echo \"==> \${name}.txt\"
            pip-compile --quiet ${PIP_COMPILE_FLAGS} \
                --output-file=\${name}.txt ${extra_args} \${name}.in
        done
    "
