#!/bin/sh

echo "Priprava databaze..."

psql -f priprava_db.sql
