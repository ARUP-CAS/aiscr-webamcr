import psycopg2 # Python library for database connection

t_host = "localhost"
t_port = "5432"
t_dbname = "test_db_2"
t_name_user = "test_user"
t_password = "test_secretpass"
db_conn = psycopg2.connect(host=t_host, port=t_port, dbname=t_dbname, user=t_name_user, password=t_password)
db_cursor = db_conn.cursor()


def get_table_list():
    s = "SELECT table_schema, table_name FROM information_schema.tables"
    db_cursor.execute(s)
    list_tables = db_cursor.fetchall()
    for t_name_table in list_tables:
        print(t_name_table + "\n")

get_table_list()
