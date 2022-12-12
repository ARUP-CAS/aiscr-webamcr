#!/usr/bin/env bash
limit=$(psql -qtAX -U postgres -c "SELECT rolconnlimit FROM pg_roles WHERE rolname='${DB_FLAG_ROLE}'")
if [ $limit == "-1" ]; then
  exit 0
else
  exit 1
fi
