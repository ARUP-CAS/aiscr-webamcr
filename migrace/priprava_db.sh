#!/bin/sh

echo "Priprava databaze..."

psql -d prod_zaloha -f priprava_db.sql
