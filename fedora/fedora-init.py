"""Inicializace základní struktury repozitáře Fedora pro AMČR instance.

Skript vytváří základní kontejnery, ACL pravidla a schéma metadat
pro produkční i testovací prostředí.
"""

import os
import time
import xml.etree.ElementTree as ET

import requests


def get_password():
    """Načte heslo uživatele `fedoraAdmin` ze souboru se secrets."""
    soubor_xml = "/var/run/secrets/tomcat_users"
    strom = ET.parse(soubor_xml)
    root = strom.getroot()
    user = root.find("user", {"name": "fedoraAdmin"})
    heslo = user.attrib["password"]
    return heslo


PASSWORD = get_password()


API_URL = "http://localhost:8080/rest"
# FEDORA_SERVER_NAME = "AMCR-selenium-test"
# FEDORA_SERVER_NAME = "AMCR"
AUTH = requests.auth.HTTPBasicAuth("fedoraAdmin", PASSWORD)


def create_new_transaction():
    """Založí novou transakci ve Fedora API a vrátí její URL."""
    print("create_new_transaction")
    response = requests.post(API_URL + "/fcr:tx", auth=AUTH, timeout=10)
    print(response)
    return response.headers["link"].split(";")[0][1:-1]


def commit(Atomic_ID):
    """Potvrdí (commitne) otevřenou Fedora transakci.

    :param Atomic_ID: URL identifikátor otevřené transakce.
    """
    print("commit")
    response = requests.put(Atomic_ID, auth=AUTH, timeout=10)
    print(response)


def create_container(Atomic_ID, name, path=""):
    """Vytvoří LDP kontejner v zadané cestě a vrátí jeho URL.

    :param Atomic_ID: URL identifikátor otevřené transakce.
    :param name: Název kontejneru předávaný v hlavičce ``Slug``.
    :param path: Cesta v repozitáři, pod kterou se kontejner vytvoří.
    :return: URL nově vytvořeného kontejneru.
    """
    print("create container ", name)
    headers = {
        "Atomic-ID": Atomic_ID,
        "Slug": name,
    }
    response = requests.post(f"{API_URL}/{path}", auth=AUTH, headers=headers, timeout=10)
    print(response)
    print(response.headers["link"].split(";")[0][1:-1])
    return response.headers["link"].split(";")[0][1:-1]


def createFedoraWebacAcl(container_path, Atomic_ID, file):
    """Nahraje ACL definici ve formátu Turtle do kontejneru Fedora.

    :param container_path: URL cílového kontejneru ve Fedora API.
    :param Atomic_ID: URL identifikátor otevřené transakce.
    :param file: Cesta k Turtle souboru s ACL pravidly.
    """
    print("createFedoraWebacAcl")
    headers = {"Atomic-ID": Atomic_ID, "Content-Type": "text/turtle"}
    with open(file, "r") as f:
        data = f.read()
        data = data.replace("/AMCR/", f"/{FEDORA_SERVER_NAME}/")
    response = requests.put(container_path + "/fcr:acl", auth=AUTH, headers=headers, data=data, timeout=10)
    print(response)


def upload_file(Atomic_ID, file, type, path):
    """Nahraje binární soubor na zadanou cestu ve Fedora repozitáři.

    :param Atomic_ID: URL identifikátor otevřené transakce.
    :param file: Cesta k lokálnímu souboru, který se má nahrát.
    :param type: MIME typ souboru použitý v hlavičce ``Content-Type``.
    :param path: Relativní cesta cílového objektu v repozitáři.
    """
    print("upload_file")
    with open(file, "rb") as f:
        data = f.read()
    headers = {
        "Atomic-ID": Atomic_ID,
        "Content-Type": type,
        "filename": f'"{os.path.basename(file)}"',
    }
    response = requests.put(f"{API_URL}/{path}", auth=AUTH, headers=headers, data=data, timeout=10)
    print(response)


def IndirectContainer(container_path, Atomic_ID, name, file):
    """Vytvoří nepřímý LDP kontejner z Turtle šablony.

    :param container_path: URL rodičovského kontejneru.
    :param Atomic_ID: URL identifikátor otevřené transakce.
    :param name: Název nového nepřímého kontejneru.
    :param file: Cesta k Turtle šabloně nepřímého kontejneru.
    """
    print("IndirectContainer")
    with open(file, "r") as f:
        data = f.read()
        data = data.replace("/AMCR/", f"/{FEDORA_SERVER_NAME}/")
    headers = {
        "Atomic-ID": Atomic_ID,
        "Slug": name,
        "Link": '<http://www.w3.org/ns/ldp#IndirectContainer>;rel="type"',
        "Content-Type": "text/turtle",
    }
    response = requests.post(container_path, auth=AUTH, headers=headers, data=data, timeout=10)
    print(response)


def get_container_content(container_path):
    """Vrátí HTTP status a seznam členů (`ldp:contains`) kontejneru.

    :param container_path: URL kontejneru, jehož obsah se načítá.
    :return: Dvojice ```(status_code, members)```.
    """
    headers = {}
    response = requests.get(container_path, auth=AUTH, headers=headers, timeout=10)
    members = []
    if response.status_code == 200:
        res_text = response.text.split("\n")
        for n in res_text:
            if "ldp:contains" in n:
                start = n.find("<")
                end = n.find(">", start)
                if start != -1 and end != -1:
                    result = n[start + 1 : end]
                    members.append(result)
    return response.status_code, members


def delete_container(container_path):
    """Odstraní zadaný kontejner.

    :param container_path: URL kontejneru určeného ke smazání.
    """
    response = requests.delete(container_path, auth=AUTH, timeout=10)
    print(response.text)


def purge_container(container_path):
    """Odstraní tombstone po předchozím smazání kontejneru.

    :param container_path: URL původního kontejneru bez suffixu ``/fcr:tombstone``.
    """
    response = requests.delete(container_path + "/fcr:tombstone", auth=AUTH, timeout=10)
    print(response.text)


def wipe_Fedora():
    """Smaže obsah hlavních model/record větví a vyčistí tombstones."""
    code, mem = get_container_content(f"{API_URL}/{FEDORA_SERVER_NAME}/model")
    for item in mem:
        items = get_container_content(item + "/member")
        for i in items:
            delete_container(i)
            purge_container(i)

    code, mem = get_container_content(f"{API_URL}/{FEDORA_SERVER_NAME}/record")
    for item in mem:
        delete_container(item)
        purge_container(item)


def generate_base_struct():
    """Vytvoří kompletní základní adresářovou a ACL strukturu AMČR."""
    path = os.path.dirname(__file__)
    transaction_id = create_new_transaction()
    createFedoraWebacAcl(API_URL, transaction_id, os.path.join(path, "inputs/acl/root-authorization.ttl"))
    c_path = create_container(transaction_id, f"{FEDORA_SERVER_NAME}")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/repo.ttl"))
    upload_file(
        transaction_id,
        os.path.join(path, "inputs/amcr.xsd"),
        "application/xml",
        f"{FEDORA_SERVER_NAME}/metadata-schema",
    )
    c_path = create_container(transaction_id, "model", f"{FEDORA_SERVER_NAME}/")

    c_path = create_container(transaction_id, "deleted", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/deleted.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-deleted.ttl"))

    c_path = create_container(transaction_id, "projekt", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-projekt.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-projekt.ttl"))

    c_path = create_container(transaction_id, "archeologicky_zaznam", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-archeologicky_zaznam.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-archeologicky_zaznam.ttl"))

    c_path = create_container(transaction_id, "let", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-let.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-let.ttl"))

    c_path = create_container(transaction_id, "adb", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-adb.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-adb.ttl"))

    c_path = create_container(transaction_id, "dokument", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-dokument.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-dokument.ttl"))

    c_path = create_container(transaction_id, "ext_zdroj", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-ext_zdroj.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-ext_zdroj.ttl"))

    c_path = create_container(transaction_id, "pian", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-pian.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-pian.ttl"))

    c_path = create_container(transaction_id, "samostatny_nalez", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-samostatny_nalez.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-samostatny_nalez.ttl"))

    c_path = create_container(transaction_id, "uzivatel", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-uzivatel.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-uzivatel.ttl"))

    c_path = create_container(transaction_id, "heslo", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-heslo.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-heslo.ttl"))

    c_path = create_container(transaction_id, "ruian_kraj", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-ruian_kraj.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-ruian_kraj.ttl"))

    c_path = create_container(transaction_id, "ruian_okres", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-ruian_okres.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-ruian_okres.ttl"))

    c_path = create_container(transaction_id, "ruian_katastr", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-ruian_katastr.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-ruian_katastr.ttl"))

    c_path = create_container(transaction_id, "organizace", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-organizace.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-organizace.ttl"))

    c_path = create_container(transaction_id, "osoba", f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/m-osoba.ttl"))
    IndirectContainer(c_path, transaction_id, "member", os.path.join(path, "inputs/ldp/indir-osoba.ttl"))

    c_path = create_container(transaction_id, "record", f"{FEDORA_SERVER_NAME}/")
    createFedoraWebacAcl(c_path, transaction_id, os.path.join(path, "inputs/acl/record.ttl"))
    commit(transaction_id)


def inicialize_base_directory():
    """Inicializuje kořenovou strukturu repozitáře po startu služby."""
    for attempt in range(MAX_RETRIES + 1):  # Pokusíme se `MAX_RETRIES + 1`krát (včetně prvního pokusu).
        try:
            stat, res = get_container_content(f"{API_URL}/{FEDORA_SERVER_NAME}")
            # Pokud server odpoví kódem 200, základní struktura již existuje.
            print(f"stat {stat}")
            if stat == 503:
                time.sleep(RETRY_DELAY)
            elif stat == 200:
                print("fedora-init.py: Základní struktura existuje")

                break
            else:
                print("fedora-init.py: Vytvářím základní strukturu")
                generate_base_struct()
                break
        except requests.exceptions.RequestException as e:
            # Při chybě spojení vypíše detail problému a čeká před dalším pokusem.
            print(f"fedora-init.py: Chyba při pokusu o spojení s Fedorou na adrese {API_URL}/{FEDORA_SERVER_NAME}: {e}")
            if attempt < MAX_RETRIES:
                print(f"fedora-init.py: Opakuji pokus {attempt + 1} za {RETRY_DELAY} sekund...")
                time.sleep(RETRY_DELAY)
            else:
                print("fedora-init.py: Vyčerpán maximální počet pokusů spojení s Fedorou.")


FEDORA_SERVER_NAME = "AMCR"

MAX_RETRIES = 10  # Maximální počet pokusů
RETRY_DELAY = 5  # Pauza mezi pokusy v sekundách
time.sleep(10)
inicialize_base_directory()

FEDORA_SERVER_NAME = "AMCR-selenium-test"
inicialize_base_directory()
