#!/bin/bash

python3 manage.py migrate
python3 manage.py set_database_rights
python3 manage.py runserver 0.0.0.0:8000
