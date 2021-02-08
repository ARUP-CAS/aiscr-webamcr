# pip install psycopg2

import hashlib
import secrets

import psycopg2
from django.contrib.auth.hashers import PBKDF2PasswordHasher


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        hashff = super().encode(sha1_hash, salt, iterations)
        return hashff

    def encode(self, password, salt, iterations=None):
        sha1_hash = hashlib.sha1(password.encode("utf8")).hexdigest()
        return self.encode_sha1_hash(sha1_hash, salt, iterations)


def encrypt_passwords(cursor, connection):
    sha1 = ""
    cursor.execute("select id, sha_1 from auth_user;")
    sha1 = cursor.fetchall()
    hasher = PBKDF2WrappedSHA1PasswordHasher()
    for hash in sha1:
        # This is working
        sha1_hash = hash[1]
        salt = secrets.token_hex(16)
        sha256 = hasher.encode_sha1_hash(sha1_hash, salt)
        cursor.execute(
            "update auth_user set password = '{}' where id = {};".format(
                sha256, hash[0]
            )
        )
        connection.commit()
        print(sha256)


try:
    connection = psycopg2.connect(
        user="", password="", host="192.168.254.21", port="5432", database="prod_zaloha"
    )

    cursor = connection.cursor()
    # Print PostgreSQL Connection properties
    print(connection.get_dsn_parameters(), "\n")

    encrypt_passwords(cursor, connection)

except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    # closing database connection.
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
