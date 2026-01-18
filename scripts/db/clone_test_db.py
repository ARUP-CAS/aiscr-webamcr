# /usr/bin/python3
import json

import psycopg2

f = open("/run/secrets/db_conf")
data = json.load(f)
f.close()
db_name = data["DB_NAME"]
db_pass = data["DB_PASS"]
db_user = data["DB_USER"]
db_host = data["DB_HOST"]
db_port = data["DB_PORT"]

prod_conn = psycopg2.connect(
    host=db_host,
    database=db_name,
    user=db_user,
    password=db_pass,
    port=db_port,
)
base_test_database = "base_test_vzor"
test_database = "test_vzor"
prod_conn.autocommit = True
prod_cursor = prod_conn.cursor()
prod_cursor.execute(
    f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{test_database}' AND pid <> pg_backend_pid();"
)
prod_cursor.execute(f"DROP DATABASE IF EXISTS {test_database};")
prod_cursor.execute(
    f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{base_test_database}' AND pid <> pg_backend_pid();"
)
prod_cursor.execute(f"CREATE DATABASE {test_database}  WITH TEMPLATE {base_test_database} strategy FILE_COPY;")
prod_conn.commit()
