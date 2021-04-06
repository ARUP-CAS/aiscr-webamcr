from dal import autocomplete
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


def heslar_12(druha, prvni_kat):
    druha = (
        Heslar.objects.filter(nazev_heslare=druha)
        .order_by("razeni")
        .values("id", "hierarchie__heslo_nadrazene", "heslo")
    )
    prvni = (
        Heslar.objects.filter(nazev_heslare=prvni_kat)
        .order_by("razeni")
        .values("id", "heslo")
    )
    return merge_heslare(prvni, druha)
