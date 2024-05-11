#!/bin/bash
#spsteni selenium tersů
# -f provede neuspesne testy
# -a provede vsechny testy
mode="a"
usage() {
  echo "Použití: $0 [-f] [-a] [-h]"
  echo "  -f    provede neuspesne testy 'f' v tabulce "
  echo "  -a    provede vsechny testy 'a' (výchozí)"
  echo "  -h    Zobrazí tuto nápovědu"
  echo " vysledky ulozi do /opt/selenium_test/results.xlsx,"
  echo "v /opt/selenium_test/ se ukladaji take screenshoty kazdeho testu "
  exit 1
}


test_all(){
docker exec -t -i $(docker ps -q -f name=swarm_webamcr_web)  python3 run_tests.py
}
test_failed(){

 docker exec -t -i $(docker ps -q -f name=swarm_webamcr_web)  python3 run_tests.py -f   
}


while getopts 'fah' flag; do
  case "${flag}" in
    f) mode="f" ;;
    a) mode="a" ;;
    h) usage ;;
    *) usage ;;
  esac
done

if [ $OPTIND -eq 1 ]; then
  mode="a"
fi

echo "Vybraný režim: $mode"

if [ "$mode" == "f" ]; then
  echo "Testuji pouze neuspesne."
  test_failed
elif [ "$mode" == "a" ]; then
  echo "Testuji vse."
  test_all
fi