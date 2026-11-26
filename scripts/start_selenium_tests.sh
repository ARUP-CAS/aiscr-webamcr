#!/bin/bash
# Foreground execution preserves the runner status; background mode only acknowledges launch.
set -euo pipefail
mode="a"
t_value=""
usage() {
  echo "Použití: $0 [-a|-f|-t cislo|-b] [-h]"
  echo "Výsledky: /opt/selenium_test/current/, předchozí běh v previous/; kořenový results.xlsx slouží výběru."
}
while getopts 'fabt:h' flag; do
  case "$flag" in
    f|a|b) mode="$flag" ;;
    t)
      [[ "$OPTARG" =~ ^[0-9]+$ ]] || { usage >&2; exit 1; }
      mode="t"; t_value="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage >&2; exit 1 ;;
  esac
done
source "$(dirname "${BASH_SOURCE[0]}")/deployment_helpers.sh"
container="$(find_dev_web_container)"
docker_env=(-e "AMCR_TEST_ATTEMPT_ID=${AMCR_TEST_ATTEMPT_ID:-}")
if [[ -n "${AMCR_TEST_RESULTS_ROOT:-}" ]]; then
  docker_env+=(-e "AMCR_TEST_RESULTS_ROOT=$AMCR_TEST_RESULTS_ROOT")
fi
command="python3 run_tests.py"
case "$mode" in
  f) command+=" -f" ;;
  t) command+=" -t $t_value" ;;
  b) command+=" -s" ;;
esac
echo "Vybraný režim: $mode"
if [[ "$mode" == b ]]; then
  nohup docker exec "${docker_env[@]}" "$container" script -e -q -c "$command" \
    < /dev/null >> /opt/selenium_test/run.log 2>&1 &
else
  docker exec "${docker_env[@]}" "$container" script -e -q -c "$command" < /dev/null
fi
