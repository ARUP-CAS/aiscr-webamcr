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
PIP_TOOLS_VERSION="7.6.1"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Pořadí je důležité: test/dev/docs používají předchozí .txt jako constraint (-c).
# Argumenty skriptu se escapují, aby přežily vložení do příkazu kontejneru.
extra_args=""
for arg in "$@"; do
    extra_args+=" $(printf '%q' "$arg")"
done

MSYS_NO_PATHCONV=1 docker run --rm \
    -v "${repo_root}/webclient:/webclient" \
    -w /webclient \
    -e CUSTOM_COMPILE_COMMAND="scripts/compile_requirements.sh" \
    "${PYTHON_IMAGE}" \
    bash -euo pipefail -c "
        pip install --quiet --root-user-action=ignore pip-tools==${PIP_TOOLS_VERSION}
        for name in requirements requirements-test requirements-dev requirements-docs; do
            echo \"==> \${name}.txt\"
            pip-compile --quiet --allow-unsafe --strip-extras --no-emit-index-url \
                --output-file=\${name}.txt ${extra_args} \${name}.in
        done
    "
