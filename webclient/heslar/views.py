from heslar.hesla import HESLAR_TYP_AKCE_DRUHA, HESLAR_TYP_AKCE_PRVNI
from heslar.models import Heslar


def merge_heslare(first, second):
    data = [("", "")]
    for k in first:
        druhy_kategorie = []
        for druh in second:
            if druh["hierarchie__heslo_nadrazene"] == k["id"]:
                druhy_kategorie.append((druh["id"], druh["heslo"]))
        data.append((k["heslo"], tuple(druhy_kategorie)))
    return data


def heslar_typ_akce_12():
    druha = (
        Heslar.objects.filter(nazev_heslare=HESLAR_TYP_AKCE_DRUHA)
        .order_by("razeni")
        .values("id", "hierarchie__heslo_nadrazene", "heslo")
    )
    prvni = (
        Heslar.objects.filter(nazev_heslare=HESLAR_TYP_AKCE_PRVNI)
        .order_by("razeni")
        .values("id", "heslo")
    )
    return merge_heslare(prvni, druha)
