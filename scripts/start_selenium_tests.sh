#!/bin/bash
#spsteni selenium tersů
# -f provede neuspesne testy
# -a provede vsechny testy
mode="a"
usage() {
  echo "Použití: $0 [-f] [-a] [-h]"
  echo "  -f          provede neuspesne testy v tabulce "
  echo "  -a          provede vsechny testy (výchozí)"
  echo "  -t cislo    provede test zadaneho cisla "
  echo "  -b          spusti všechny testy na pozadí, výstup se uloží do /opt/selenium_test/test.log a run.log"
  echo "  -h          Zobrazí tuto napovedu"
  echo " vysledky ulozi do /opt/selenium_test/results.xlsx,"
  echo "v /opt/selenium_test/ se ukladaji take screenshoty kazdeho testu "
  exit 1
}


test_all(){
docker exec -t -i $(docker ps -q -f name=swarm_webamcr_web)  python3 run_tests.py
}

test_all_background(){
nohup docker exec $(docker ps -q -f name=swarm_webamcr_web)  python3 run_tests.py -s >>/opt/selenium_test/run.log 2>&1 &
}

test_failed(){
docker exec -t -i $(docker ps -q -f name=swarm_webamcr_web)  python3 run_tests.py -f 
}

test_number(){
docker exec -t -i $(docker ps -q -f name=swarm_webamcr_web)  python3 run_tests.py -t $1  
}


while getopts 'fabt:h' flag; do
  case "${flag}" in
    f) mode="f" ;;
    a) mode="a" ;;
    b) mode="b" ;;
    t) 
      if ! [[ $OPTARG =~ ^[0-9]+$ ]]; then
        echo "Chyba: parametr -t vyzaduje cislo."
        usage
      fi
      mode="t"
      t_value=$OPTARG
      ;;
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
elif [ "$mode" == "t" ]; then
  echo "Testuji test $t_value."
  test_number $t_value
elif [ "$mode" == "b" ]; then
  echo "Testuji vse na pozadi"
  test_all_background
fi