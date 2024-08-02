#!/bin/bash

python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:8000
python3 manage.py shell < data_management.py
