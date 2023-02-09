from datetime import datetime, date

import psycopg2
from psycopg2 import OperationalError
import psycopg2.extras
from tqdm import tqdm
import json


def write_to_log(record):
    with open("outpout.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def execute_read_query(connection, query):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except OperationalError as e:
        print(f"The error '{e}' occurred")


def process_value(value):
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    if value is None:
        return "null"
    if isinstance(value, datetime) or isinstance(value, date):
        return "'" + str(value) + "'"
    return str(value)


def write_group(connection, table, records):
    columns = [i for i in records[0].keys()]
    values = ["(" + ",".join([process_value(j) for j in record.values()]) + ")" for record in records]
    columns = ", ".join(columns)
    insert_query = f"INSERT INTO {table} ({columns}) VALUES {', '.join(values)};"
    cursor = connection.cursor()
    try:
        cursor.execute(insert_query)
    except psycopg2.errors.NotNullViolation as err:
        write_to_log({"error": "NotNullViolation", "table": table, "err": str(err)})
        connection.rollback()
    except psycopg2.errors.NumericValueOutOfRange as err:
        write_to_log({"error": "NumericValueOutOfRange", "table": table, "err": str(err)})
        connection.rollback()
    except psycopg2.errors.UniqueViolation as err:
        write_to_log({"error": "UniqueViolation", "table": table,  "err": str(err)})
        connection.rollback()
    except psycopg2.errors.UndefinedColumn as err:
        write_to_log({"error": "UndefinedColumn", "table": table, "err": str(err)})
        connection.rollback()
    except psycopg2.errors.StringDataRightTruncation as err:
        write_to_log({"error": "StringDataRightTruncation", "table": table, "err": str(err)})
        connection.rollback()


def process_tables(con_source, con_dest, tables):
    for table in tables:
        truncate_query = f"TRUNCATE {table} CASCADE;"
        cursor = con_dest.cursor()
        cursor.execute(truncate_query)
        con_dest.commit()
        select_query = f"SELECT * FROM {table}"
        records = execute_read_query(con_source, select_query)
        if len(records) > 0:
            for i in tqdm(range(0, len(records), 1000), desc=table):
                write_group(con_dest, table, records[i:min(i+1000, len(records))])
        try:
            con_dest.commit()
        except psycopg2.errors.ForeignKeyViolation as err:
            print(err)
            con_dest.rollback()


with open("data_backup_connections.json", encoding="utf-8") as file:
    connection_data = json.load(file)
con_source = create_connection(
    connection_data["source"]["database_name"],
    connection_data["source"]["username"],
    connection_data["source"]["password"],
    connection_data["source"]["host"],
    connection_data["source"]["port"]
)
con_dest = create_connection(
    connection_data["destination"]["database_name"],
    connection_data["destination"]["username"],
    connection_data["destination"]["password"],
    connection_data["destination"]["host"],
    connection_data["destination"]["port"]
)

tables = (
    "odstavky_systemu",
    "heslar_nazev",
    "heslar",
    "heslar_datace",
    "heslar_dokument_typ_material_rada",
    "heslar_hierarchie",
    "heslar_odkaz",
    "osoba",
    "organizace",
    "historie_vazby",
    "auth_user",
    "auth_group",
    "uzivatel_historicaluser",
    "django_content_type",
    "auth_permission",
    "auth_group_permissions",
    "auth_user_groups",
    "auth_user_user_permissions",
    "notifikace_typ",
    "auth_user_notifikace_typ",
    "historie",
    "kladysm5",
    "kladyzm",
    "ruian_kraj",
    "ruian_okres",
    "pian_sekvence",
    "pian",
    "ruian_katastr",
    "let",
    "soubor_vazby",
    "soubor",
    "dokument_sekvence",
    "dokument",
    "dokument_autor",
    "dokument_extra_data",
    "dokument_jazyk",
    "dokument_osoba",
    "dokument_posudek",
    "tvar",
    "archeologicky_zaznam",
    "archeologicky_zaznam_katastr",
    "projekt_sekvence",
    "projekt",
    "projekt_katastr",
    "oznamovatel",
    "akce",
    "akce_vedouci",
    "lokalita",
    "komponenta_vazby",
    "dokument_cast",
    "neident_akce",
    "neident_akce_vedouci",
    "komponenta",
    "komponenta_aktivita",
    "nalez_objekt",
    "nalez_predmet",
    "dokumentacni_jednotka",
    "adb_sekvence",
    "adb",
    "vyskovy_bod",
    "externi_zdroj",
    "externi_zdroj_autor",
    "externi_zdroj_editor",
    "externi_odkaz",
    "samostatny_nalez",
    "uzivatel_spoluprace",
    "watchdog_watchdog",
)
process_tables(con_source, con_dest, tables)

