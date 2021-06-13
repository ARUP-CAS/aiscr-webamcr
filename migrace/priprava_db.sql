drop database if exists prod_zaloha;

CREATE DATABASE prod_zaloha
    WITH
    OWNER = cz_archeologickamapa_api
    TEMPLATE = prod_zaloha_backup
    ENCODING = 'UTF8';
