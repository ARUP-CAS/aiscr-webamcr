import json
import logging

from core.setting_models import CustomAdminSettings
from heslar.models import Heslar
from uzivatel.models import Organizace, Osoba

logger = logging.getLogger(__name__)


def get_id_from_heslar(ident_cely):
    try:
        pk = Heslar.objects.get(ident_cely=ident_cely).pk
        return pk
    except Exception:
        # This will happen when automated tests are run
        return int(ident_cely.replace("HES-", ""))


def get_id_from_organizace(ident_cely):
    try:
        pk = Organizace.objects.get(ident_cely=ident_cely).pk
        return pk
    except Exception:
        # This will happen when automated tests are run
        return int(ident_cely.replace("ORG-", ""))


def get_id_from_osoba(ident_cely):
    try:
        pk = Osoba.objects.get(ident_cely=ident_cely).pk
        return pk
    except Exception:
        # This will happen when automated tests are run
        return int(ident_cely.replace("OS-", ""))


def get_settings(item_group, item_id):
    settings_query = CustomAdminSettings.objects.filter(item_group=item_group, item_id=item_id)
    if settings_query.count() > 0:
        return json.loads(settings_query.last().value)
    return {}


heslar = get_settings("constants", "heslar")
for key, value in heslar.items():
    if key in globals():
        logger.warning("heslar.hesla_dynamicka.heslar.variable_exist", extra={"key": key})
    globals()[key] = get_id_from_heslar(value)

heslar_group = get_settings("constants", "heslar_group")
for key, values in heslar_group.items():
    group = []
    for val in values:
        group.append(globals().get(val))
    if key in globals():
        logger.warning("heslar.hesla_dynamicka.heslar_group.variable_exist", extra={"key": key})
    globals()[key] = group

organizace = get_settings("constants", "organizace")
for key, value in organizace.items():
    if key in globals():
        logger.warning("heslar.hesla_dynamicka.organizace.variable_exist", extra={"key": key})
    globals()[key] = get_id_from_organizace(value)

organizace_group = get_settings("constants", "organizace_group")
for key, values in organizace_group.items():
    group = []
    for val in values:
        group.append(globals().get(val))
    if key in globals():
        logger.warning("heslar.hesla_dynamicka.organizace_group.variable_exist", extra={"key": key})
    globals()[key] = group

osoba = get_settings("constants", "osoba")
for key, value in osoba.items():
    if key in globals():
        logger.warning("heslar.hesla_dynamicka.osoba.variable_exist", extra={"key": key})
    globals()[key] = get_id_from_heslar(value)

osoba_group = get_settings("constants", "osoba_group")
for key, values in osoba_group.items():
    group = []
    for val in values:
        group.append(globals().get(val))
    if key in globals():
        logger.warning("heslar.hesla_dynamicka.osoba_group.variable_exist", extra={"key": key})
    globals()[key] = group
