#!/bin/sh

./priprava_db.sh || exit

mv migrace_all.log migrace_all.log.`date "+%d%m%Y_%H%M%S"` || exit

./migrace_all.sh 2>&1 | tee --append migrace_all.log
