import datetime
import hashlib
import secrets
import sys
import traceback

import psycopg2
from django.contrib.auth.hashers import PBKDF2PasswordHasher

SOURCE_DB_NAME = "django_migrated_db_source_db"
DEFAULT_BATCH_SIZE = 10000
TABLE_BATCH_SIZE = {"dokument_sekvence": 10 ** 4, "dokument_jazyk": 10 ** 4}


def item_to_str(item):
    if item is None:
        return "null"
    if isinstance(item, str):
        item = item.replace("'", "''")
        return f"'{item}'"
    if isinstance(item, datetime.datetime) or isinstance(item, datetime.date):
        return f"'{item}'"
    return str(item)


def write_batch(table_name, column_names, query_data, destination_cursor, destination_conn):
    if len(query_data):
        query_data = ", ".join(query_data)
        query = f"INSERT INTO public.{table_name} ({', '.join(column_names)}) VALUES {query_data};"
        try:
            destination_cursor.execute(query)
        except psycopg2.IntegrityError as err:
            print(err)
            print(query)
        destination_conn.commit()


def copy_data(source_host, destination_host, source_db, destination_db, source_user, destination_user, source_password,
              destination_password, truncate_all=False):
    source_conn = None
    destination_conn = None
    source_cursor = None
    destination_cursor = None
    try:
        source_conn = psycopg2.connect(
            host=source_host,
            database=source_db,
            user=source_user,
            password=source_password
        )

        # establish connection to test_prod_zaloha database
        destination_conn = psycopg2.connect(
            host=destination_host,
            database=destination_db,
            user=destination_user,
            password=destination_password
        )

        source_cursor = source_conn.cursor()
        destination_cursor = destination_conn.cursor()

        # execute SQL query to copy data from prod_zaloha.ruian_katastr to test_prod_zaloha.ruian_katastr
        tables = (
            ("*", "odstavky_systemu"),
            ("*", "heslar_nazev"),
            ("*", "heslar"),
            ("*", "heslar_datace"),
            ("*", "heslar_dokument_typ_material_rada"),
            ("*", "heslar_hierarchie"),
            ("*", "heslar_odkaz"),
            ("*", "osoba"),
            ("*", "organizace"),
            ("*", "historie_vazby"),
            ("*", "auth_user"),
            ("*", "auth_group"),
            ("id, ident_cely, zasilat_neaktivnim, predmet, COALESCE(cesta_sablony, 'X') AS cesta_sablony",
             "notifikace_typ"),
            ("*", "auth_user_notifikace_typ"),
            ("*", "historie"),
            ("*", "kladysm5"),
            ("*", "kladyzm"),
            ("*", "ruian_kraj"),
            ("*", "ruian_okres"),
            ("*", "pian_sekvence"),
            ("*", "pian"),
            ("*", "ruian_katastr", "WHERE soucasny IS NULL"),
            ("*", "ruian_katastr", "WHERE soucasny IS NOT NULL"),
            ("*", "let"),
            ("*", "soubor_vazby"),
            ("*", "soubor"),
            ("*", "dokument_sekvence"),
            (
            "id, rok_vzniku, popis, poznamka, oznaceni_originalu, stav, ident_cely, datum_zverejneni, licence, historie, let, material_originalu, organizace, pristupnost, rada, soubory, typ_dokumentu, ulozeni_originalu",
            "dokument"),
            ("*", "dokument_autor"),
            ("*", "dokument_extra_data"),
            ("*", "dokument_jazyk"),
            ("*", "dokument_osoba"),
            ("*", "dokument_posudek"),
            ("*", "archeologicky_zaznam"),
            ("*", "archeologicky_zaznam_katastr"),
            ("*", "projekt_sekvence"),
            ("*", "projekt"),
            ("*", "projekt_katastr"),
            ("*", "oznamovatel"),
            ("*", "akce"),
            ("*", "akce_vedouci"),
            ("*", "lokalita"),
            ("*", "komponenta_vazby"),
            ("*", "dokument_cast"),
            ("*", "neident_akce"),
            ("*", "neident_akce_vedouci"),
            ("*", "komponenta"),
            ("*", "komponenta_aktivita"),
            ("*", "nalez_objekt"),
            ("*", "nalez_predmet"),
            ("*", "dokumentacni_jednotka"),
            ("*", "adb_sekvence"),
            ("*", "adb"),
            ("*", "vyskovy_bod"),
            ("*", "externi_zdroj"),
            ("*", "externi_zdroj_autor"),
            ("*", "externi_zdroj_editor"),
            ("*", "externi_odkaz"),
            ("*", "samostatny_nalez"),
            ("*", "uzivatel_spoluprace"),
            ("*", "auth_user_groups"),
            ("*", "tvar"),
        )
        table_names = [i[1] for i in tables]
        table_names.reverse()
        finished_tables = set()
        incomplete_tables = set()
        for item in table_names:
            if item in incomplete_tables:
                continue
            source_cursor.execute(f"SELECT COUNT(*) FROM public.{item}")
            source_result = source_cursor.fetchone()
            destination_cursor.execute(f"SELECT COUNT(*) FROM public.{item}")
            destination_result = destination_cursor.fetchone()
            if source_result != destination_result or truncate_all is True:
                destination_cursor.execute(f"TRUNCATE TABLE public.{item} CASCADE;")
                destination_conn.commit()
                print(f"Truncated table: {item}.")
                if item in finished_tables:
                    finished_tables.remove(item)
            else:
                finished_tables.add(item)
        finished_tables = finished_tables - incomplete_tables
        for item in tables:
            if item[1] in finished_tables:
                print(f"Skipping table: {item[1]}")
                continue
            if len(item) == 2:
                condition = ""
                print(f"Processing table: {item[1]}")
            else:
                condition = item[2]
                print(f"Processing table: {item[1]}, condition: {condition}")
            source_cursor.execute(f"SELECT {item[0]} FROM public.{item[1]} {condition}")
            column_names = [desc[0] for desc in source_cursor.description]
            batch_number = 0
            query_data = []
            batch_size = TABLE_BATCH_SIZE.get(item[1], DEFAULT_BATCH_SIZE)
            for row in source_cursor:
                batch_number += 1
                row = f"({', '.join([item_to_str(item) for item in row])})"
                query_data = query_data + [row]
                if batch_number % batch_size == 0:
                    write_batch(item[1], column_names, query_data, destination_cursor, destination_conn)
                    query_data = []
                    print(f"Writing record {batch_number} of {source_cursor.rowcount}.")
            write_batch(item[1], column_names, query_data, destination_cursor, destination_conn)
            print(f"Table finished: {item}. Written records: {batch_number}.")
    except Exception as err:
        print(err)
        traceback.print_exc()
    finally:
        if source_cursor is not None:
            source_cursor.close()
        if destination_cursor is not None:
            destination_cursor.close()
        if source_conn is not None:
            source_conn.close()
        if destination_conn is not None:
            destination_conn.close()


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        hashff = super().encode(sha1_hash, salt, iterations)
        return hashff

    def encode(self, password, salt, iterations=None):
        sha1_hash = hashlib.sha1(password.encode("utf8")).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)


def encrypt_passwords(destination_host, destination_db, destination_user, destination_password):
    destination_conn = psycopg2.connect(
        host=destination_host,
        database=destination_db,
        user=destination_user,
        password=destination_password
    )
    destination_cursor = destination_conn.cursor()
    destination_cursor.execute("select id, sha_1 from auth_user;")
    sha1 = destination_cursor.fetchall()
    hasher = PBKDF2WrappedSHA1PasswordHasher()
    for current_hash in sha1:
        sha1_hash = current_hash[1]
        if len(sha1_hash) == 40:
            salt = secrets.token_hex(16)
            sha256 = hasher.encode_sha1_hash(sha1_hash, salt)
            destination_cursor.execute(f"update auth_user set password = '{sha256}' where id = {current_hash[0]};")
    destination_conn.commit()
    print("Passowrds encrypted.")


def reset_sequences(destination_host, destination_db, destination_user, destination_password):
    destination_conn = psycopg2.connect(
        host=destination_host,
        database=destination_db,
        user=destination_user,
        password=destination_password
    )
    destination_cursor = destination_conn.cursor()
    tables = (
        ("id", "odstavky_systemu"),
        ("id", "heslar_nazev"),
        ("id", "heslar"),
        ("id", "heslar_dokument_typ_material_rada"),
        ("id", "heslar_hierarchie"),
        ("id", "heslar_odkaz"),
        ("id", "osoba"),
        ("id", "organizace"),
        ("id", "historie_vazby"),
        ("id", "auth_user"),
        ("id", "notifikace_typ"),
        ("id", "auth_user_notifikace_typ"),
        ("id", "historie"),
        # ("id", "kladyzm"),
        ("id", "ruian_kraj"),
        ("id", "ruian_okres"),
        ("id", "pian_sekvence"),
        ("id", "pian"),
        ("id", "ruian_katastr"),
        ("id", "let"),
        ("id", "soubor_vazby"),
        ("id", "soubor"),
        ("id", "dokument_sekvence"),
        ("id", "dokument"),
        ("id", "dokument_autor"),
        # ("id", "dokument_extra_data"),
        ("id", "dokument_jazyk"),
        ("id", "dokument_osoba"),
        ("id", "dokument_posudek"),
        ("id", "archeologicky_zaznam"),
        ("id", "archeologicky_zaznam_katastr"),
        ("id", "projekt_sekvence"),
        ("id", "projekt"),
        ("id", "projekt_katastr"),
        # ("id", "akce"),
        ("id", "akce_vedouci"),
        ("id", "komponenta_vazby"),
        ("id", "dokument_cast"),
        ("id", "neident_akce_vedouci"),
        ("id", "komponenta"),
        ("id", "komponenta_aktivita"),
        ("id", "nalez_objekt"),
        ("id", "nalez_predmet"),
        ("id", "dokumentacni_jednotka"),
        ("id", "adb_sekvence"),
        ("id", "vyskovy_bod"),
        ("id", "externi_zdroj"),
        ("id", "externi_zdroj_autor"),
        ("id", "externi_zdroj_editor"),
        ("id", "externi_odkaz"),
        ("id", "samostatny_nalez"),
        ("id", "uzivatel_spoluprace"),
        ("id", "tvar"),
    )
    for item in tables:
        destination_cursor.execute(f"SELECT SETVAL("
                                   f"(SELECT PG_GET_SERIAL_SEQUENCE('\"{item[1]}\"', '{item[0]}')),"
                                   f"(SELECT (MAX(\"{item[0]}\") + 1) FROM \"{item[1]}\"),FALSE);")
    destination_conn.commit()
    print("Sequences are set.")

if __name__ == "__main__":
    copy_data(source_host=sys.argv[1], destination_host=sys.argv[2],
              source_db=sys.argv[3], destination_db=sys.argv[4],
              source_user=sys.argv[5], destination_user=sys.argv[6],
              source_password=sys.argv[7], destination_password=sys.argv[8], truncate_all=True)
    encrypt_passwords(destination_host=sys.argv[2], destination_db=sys.argv[4], destination_user=sys.argv[6],
                      destination_password=sys.argv[8])
    reset_sequences(destination_host=sys.argv[2], destination_db=sys.argv[4], destination_user=sys.argv[6],
                      destination_password=sys.argv[8])
