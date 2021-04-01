from dal import autocomplete
from heslar.hesla import HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT
from heslar.models import Heslar, RuianKatastr


class RuianKatastrAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = RuianKatastr.objects.all()
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


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
        Heslar.objects.filter(nazev_heslare=HESLAR_AKCE_TYP)
        .order_by("razeni")
        .values("id", "hierarchie__heslo_nadrazene", "heslo")
    )
    prvni = (
        Heslar.objects.filter(nazev_heslare=HESLAR_AKCE_TYP_KAT)
        .order_by("razeni")
        .values("id", "heslo")
    )
    return merge_heslare(prvni, druha)
