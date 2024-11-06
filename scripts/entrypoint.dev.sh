#!/bin/bash

python3 manage.py migrate
#python3 manage.py runserver 0.0.0.0:8000
python manage.py runserver_plus --cert-file /cert/amcr-test-local.crt 0.0.0.0:8000
python3 manage.py shell < data_management.py