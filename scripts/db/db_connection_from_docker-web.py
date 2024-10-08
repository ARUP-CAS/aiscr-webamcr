# /usr/bin/python3
import json

import psycopg2

f = open("/run/secrets/db_conf")
data = json.load(f)
f.close()
dbn = data["DB_NAME"]
dbp = data["DB_PASS"]
dbu = data["DB_USER"]
dbh = data["DB_HOST"]

e_code = 1
conn = psycopg2.connect(f"dbname={dbn} user={dbu} host={dbh} password={dbp}")
try:
    # Establish the connection and create a cursor object

    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result[0] == 1:
            print("Database is healthy!")
            e_code = 0
        else:
            print("Database is NOT healthy!")
            e_code = 1
except Exception as e:
    print(f"Database health check FAILED: {e}")
finally:
    conn.close()

exit(e_code)
