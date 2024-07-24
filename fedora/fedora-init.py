import requests
import os
import time
import xml.etree.ElementTree as ET


def get_password():
    soubor_xml = '/var/run/secrets/tomcat_users'
    strom = ET.parse(soubor_xml)
    root = strom.getroot()
    user = root.find('user', {'name': 'fedoraAdmin'})
    heslo = user.attrib['password']
    return heslo

PASSWORD = get_password()


API_URL = "http://localhost:8080/rest/"
#FEDORA_SERVER_NAME = "AMCR-selenium-test"
#FEDORA_SERVER_NAME = "AMCR"
AUTH = requests.auth.HTTPBasicAuth('fedoraAdmin', PASSWORD)

def create_new_transaction():
    print('create_new_transaction')
    response = requests.post(API_URL+'fcr:tx',auth=AUTH, timeout=10)
    print(response)
    return response.headers['link'].split(';')[0][1:-1]


def commit(Atomic_ID):
    print('commit')   
    response = requests.put(Atomic_ID, auth=AUTH, timeout=10)
    print(response)


def create_container(Atomic_ID, name,path=''):
    print("create container ",name)
    headers =  {"Atomic-ID":Atomic_ID,"Slug": name,}
    response = requests.post(API_URL+path,auth=AUTH,headers=headers, timeout=10)
    print(response)
    print(response.headers['link'].split(';')[0][1:-1])
    return response.headers['link'].split(';')[0][1:-1]


#(FedoraAcl) PUT acl resource 'AMCR/'
#curl -u fedoraAdmin:pswd -H"Atomic-ID: http://localhost:8080/rest/fcr:tx/285ba3a5-7bce-48e0-b4a8-324da8a42a22" -X PUT http://localhost:8080/rest/AMCR/fcr:acl -H "Content-Type: text/turtle" --data-binary "@C:\Users\havrlant\Documents\ARUP\fedora\inputs\acl\repo.ttl"
def createFedoraWebacAcl(container_path,Atomic_ID,file):
    print('createFedoraWebacAcl')   
    headers =  {"Atomic-ID":Atomic_ID,"Content-Type":  'text/turtle'}
    with open(file, 'r') as f:
        data = f.read()
        data = data.replace("/rest/AMCR", f"/rest/{FEDORA_SERVER_NAME}")
    response = requests.put(container_path+'/fcr:acl',auth=AUTH,headers=headers,data=data, timeout=10)
    print(response)

#curl -u fedoraAdmin:pswd -H"Atomic-ID: http://localhost:8080/rest/fcr:tx/9afcc89d-7c5a-4bf8-91bd-4daa89b0c4eb" -X PUT --upload-file "C:/Users\havrlant\Documents\ARUP\fedora\inputs\amcr.xsd" -H "Content-Type: application/xml" -H "Content-Disposition: attachment; filename=\"amcr.xsd\"" -H "digest: sha-512=6ca8eca77bec25b701212d655b5c8d7aa582acbdfa72e7491f116d8e902b3ae0ecaa5dd8ca60cb06d57b5b5bcc7d887382f5e57d788f3928921d3ea04d10c4e7" "http://localhost:8080/rest/AMCR/metadata-schema"
def upload_file(Atomic_ID,file,type,path):
    print('upload_file')  
    with open(file, 'rb') as f:
        data = f.read() 
    headers =  {"Atomic-ID":Atomic_ID,"Content-Type": type,'filename': f"\"{os.path.basename(file)}\"",} 
    response = requests.put(API_URL+path,auth=AUTH,headers=headers,data=data, timeout=10)
    print(response)
    
    
#curl -u fedoraAdmin:pswd -X POST -H "Slug: member" -H "Link: <http://www.w3.org/ns/ldp#IndirectContainer>;rel=\"type\"" -H "Content-Type: text/turtle" --data-binary "@C:\Users\havrlant\Documents\ARUP\fedora\inputs\ldp\indir-deleted.ttl"  "http://localhost:8080/rest/AMCR/model/deleted"   
def  IndirectContainer(container_path,Atomic_ID,name,file):
    print('IndirectContainer')  
    with open(file, 'r') as f:
        data = f.read()
        data = data.replace("/rest/AMCR", f"/rest/{FEDORA_SERVER_NAME}")
    headers =  {"Atomic-ID":Atomic_ID,"Slug": name,  'Link': '<http://www.w3.org/ns/ldp#IndirectContainer>;rel="type"',"Content-Type":  'text/turtle'}
    response = requests.post(container_path,auth=AUTH,headers=headers,data=data, timeout=10)
    print(response)
    
def get_container_content(container_path):
    headers = {}
    response = requests.get(container_path,auth=AUTH,headers=headers, timeout=10)
    members=[]
    if(response.status_code==200):
        res_text = response.text.split("\n")
        for n in res_text:
            if 'ldp:contains' in n: 
                start = n.find('<')               
                end = n.find('>', start)               
                if start != -1 and end != -1:               
                    result = n[start + 1:end]          
                    members.append(result)
    return response.status_code,members
   # 'C-202401979'


def delete_container(container_path):
    response = requests.delete(container_path,auth=AUTH, timeout=10) 
    print(response.text) 

def purge_container(container_path):
    response = requests.delete(container_path+"/fcr:tombstone",auth=AUTH, timeout=10) 
    print(response.text) 

def wipe_Fedora():
    code,mem=get_container_content(f'{API_URL}{FEDORA_SERVER_NAME}/model')
    for item in mem:
        items=get_container_content(item+'/member')
        for i in items:
            delete_container(i)
            purge_container(i)
        
    code,mem=get_container_content(f'{API_URL}{FEDORA_SERVER_NAME}/record')
    for item in mem:
        delete_container(item)
        purge_container(item)
   


def generate_base_struct():
    path = os.path.dirname(__file__)
    transaction_id = create_new_transaction()
    
    c_path=create_container(transaction_id, f"{FEDORA_SERVER_NAME}")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/repo.ttl'))
    upload_file(transaction_id,os.path.join(path,'inputs/amcr.xsd'),'application/xml',f'{FEDORA_SERVER_NAME}/metadata-schema')
    c_path=create_container(transaction_id, "model",f"{FEDORA_SERVER_NAME}/")

    c_path=create_container(transaction_id, "deleted",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/deleted.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-deleted.ttl'))

    c_path=create_container(transaction_id, "projekt",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-projekt.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-projekt.ttl'))

    c_path=create_container(transaction_id, "archeologicky_zaznam",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-archeologicky_zaznam.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-archeologicky_zaznam.ttl'))

    c_path=create_container(transaction_id, "let",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-let.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-let.ttl'))

    c_path=create_container(transaction_id, "adb",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-adb.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-adb.ttl'))

    c_path=create_container(transaction_id, "dokument",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-dokument.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-dokument.ttl'))

    c_path=create_container(transaction_id, "ext_zdroj",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-ext_zdroj.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-ext_zdroj.ttl'))

    c_path=create_container(transaction_id, "pian",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-pian.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-pian.ttl'))

    c_path=create_container(transaction_id, "samostatny_nalez",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-samostatny_nalez.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-samostatny_nalez.ttl'))

    c_path=create_container(transaction_id, "uzivatel",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-uzivatel.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-uzivatel.ttl'))

    c_path=create_container(transaction_id, "heslo",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-heslo.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-heslo.ttl'))

    c_path=create_container(transaction_id, "ruian_kraj",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-ruian_kraj.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-ruian_kraj.ttl'))

    c_path=create_container(transaction_id, "ruian_okres",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-ruian_okres.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-ruian_okres.ttl'))

    c_path=create_container(transaction_id, "ruian_katastr",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-ruian_katastr.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-ruian_katastr.ttl'))

    c_path=create_container(transaction_id, "organizace",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-organizace.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-organizace.ttl'))

    c_path=create_container(transaction_id, "osoba",f"{FEDORA_SERVER_NAME}/model/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/m-osoba.ttl'))
    IndirectContainer(c_path,transaction_id,'member',os.path.join(path,'inputs/ldp/indir-osoba.ttl'))

    c_path=create_container(transaction_id, "record",f"{FEDORA_SERVER_NAME}/")
    createFedoraWebacAcl(c_path,transaction_id,os.path.join(path,'inputs/acl/record.ttl'))
    commit(transaction_id)

#FEDORA_SERVER_NAME = "AMCR-selenium-test"

FEDORA_SERVER_NAME = "AMCR"

MAX_RETRIES = 10  # Maximální počet pokusů
RETRY_DELAY = 5  # Pauza mezi pokusy v sekundách

for attempt in range(MAX_RETRIES + 1):  # Pokusíme se max_retries + 1 krát (včetně prvního pokusu)
    try:
        stat, res=get_container_content(f'{API_URL}{FEDORA_SERVER_NAME}')
        # Pokud server odpoví status kódem 200, je vše v pořádku
        if stat == 200:
            print("fedora-init.py: Základní struktura existuje")
            
            break
        else:
            print("fedora-init.py: Vytvářím základní strukturu")
            generate_base_struct()
            break
    except requests.exceptions.RequestException as e:
        # Pokud dojde k výjimce, vypíše chybu a počká 2 sekundy před dalším pokusem
        print(f"fedora-init.py: Chyba při pokusu o spojení s Fedorou na adrese {API_URL}{FEDORA_SERVER_NAME}: {e}")
        if attempt < MAX_RETRIES:
            print(f"fedora-init.py: Opakuji pokus {attempt + 1} za {RETRY_DELAY} sekund...")
            time.sleep(RETRY_DELAY)
        else:
            print("fedora-init.py: Vyčerpán maximální počet pokusů spojení s Fedorou.")
