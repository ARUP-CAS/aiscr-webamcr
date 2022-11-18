#!/bin/sh

set -e

export DJANGO_SETTINGS_MODULE=webclient.settings.dev

python3 -m pip install --upgrade pip
pip install wheel
pip install -r webclient/requirements/dev.txt

export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal

apt-get update
apt-get install -y libgdal-dev locales
gdal-config --version

pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

python3 manage.py migrate heslar --skip-checks
python3 manage.py migrate auth
python3 manage.py migrate
python3 manage.py makemigrations
python3 manage.py migrate

python3 manage.py runserver 0.0.0.0:8000
