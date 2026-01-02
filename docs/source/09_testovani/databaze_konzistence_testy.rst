Konzistence databáze
=====================

Aplikace zajišťuje konzistenci databáze s využitím signálů,
které jsou náhradou databázových triggerů. Níže je přehled testovacích scénářů,
které ověří korektní funkčnost signálů.


Prvním krokem je spuštění termínálu.

..
    python3 manage.py shell --settings=webclient.settings.dev

Pro generování identů je použita funkce `get_random_string`.

.. code:: py
    import random
    import string

    def get_random_string():
        letters = string.ascii_uppercase
        return ''.join(random.choice(letters) for i in range(8))

**delete_connected_komponenta_vazby_relations**

.. code:: py
    from komponenta.models import KomponentaVazby, Komponenta
    from heslar.models import Heslar
    kv = KomponentaVazby(typ_vazby="dokumentacni_jednotka")
    kv.save()
    k = Komponenta(obdobi=Heslar.objects.filter(nazev_heslare=15).first(), areal=Heslar.objects.filter(nazev_heslare=2).first(), komponenta_vazby=kv, ident_cely="XX")
    k.save()
    kv.delete()
    k.refresh_from_db()

**delete_connected_komponenty_relations**

.. code:: py
    from komponenta.models import KomponentaVazby, KomponentaAktivita, Komponenta
    from heslar.models import Heslar
    kv = KomponentaVazby(typ_vazby="dokumentacni_jednotka")
    kv.save()
    k = Komponenta(ident_cely="X",obdobi=Heslar.objects.filter(nazev_heslare=15).first(), areal=Heslar.objects.filter(nazev_heslare=2).first(), komponenta_vazby=kv)
    k.save()
    ka = KomponentaAktivita(komponenta=k, aktivita=Heslar.objects.filter(nazev_heslare=1).first())
    ka.save()
    k.delete()
    ka.refresh_from_db()

    from komponenta.models import KomponentaVazby, Komponenta
    from nalez.models import NalezPredmet
    from heslar.models import Heslar
    kv = KomponentaVazby(typ_vazby="dokumentacni_jednotka")
    kv.save()
    k = Komponenta(ident_cely="X",obdobi=Heslar.objects.filter(nazev_heslare=15).first(), areal=Heslar.objects.filter(nazev_heslare=2).first(), komponenta_vazby=kv)
    k.save()
    np = NalezPredmet(komponenta=k, druh=Heslar.objects.filter(nazev_heslare=22).first(), specifikace=Heslar.objects.filter(nazev_heslare=30).first())
    np.save()
    k.delete()
    np.refresh_from_db()

    from komponenta.models import KomponentaVazby, Komponenta
    from nalez.models import NalezObjekt
    from heslar.models import Heslar
    kv = KomponentaVazby(typ_vazby="dokumentacni_jednotka")
    kv.save()
    k = Komponenta(ident_cely="X",obdobi=Heslar.objects.filter(nazev_heslare=15).first(), areal=Heslar.objects.filter(nazev_heslare=2).first(), komponenta_vazby=kv)
    k.save()
    no = NalezObjekt(komponenta=k, druh=Heslar.objects.filter(nazev_heslare=17).first(), specifikace=Heslar.objects.filter(nazev_heslare=28).first())
    no.save()
    k.delete()
    no.refresh_from_db()

**delete_related_dokument_cast**

.. code:: py
    from dokument.models import Dokument, DokumentCast
    from heslar.models import Heslar
    from uzivatel.models import Organizace
    d = Dokument(rada=Heslar.objects.filter(nazev_heslare=26).first(), typ_dokumentu=Heslar.objects.filter(nazev_heslare=35).first(), organizace=Organizace.objects.first(), material_originalu=Heslar.objects.filter(nazev_heslare=12).first(), stav=1, ident_cely="XX")
    d.save()
    dc = DokumentCast(dokument=d, ident_cely="XX")
    dc.save()
    d.delete()
    dc.refresh_from_db()

    # delete_related_komponenta -> delete_komponenta_vazby

    from komponenta.models import KomponentaVazby, Komponenta
    from heslar.models import Heslar
    kv = KomponentaVazby(typ_vazby="dokumentacni_jednotka")
    kv.save()
    k = Komponenta(obdobi=Heslar.objects.filter(nazev_heslare=15).first(), areal=Heslar.objects.filter(nazev_heslare=2).first(), komponenta_vazby=kv, ident_cely="ABCDEF")
    k.save()
    k.delete()
    kv.refresh_from_db()

    # delete_related_neident_dokument_cast

    from dokument.models import Dokument, DokumentCast
    from heslar.models import Heslar
    from neidentakce.models import NeidentAkce
    from uzivatel.models import Organizace
    d = Dokument(rada=Heslar.objects.filter(nazev_heslare=26).first(), typ_dokumentu=Heslar.objects.filter(nazev_heslare=35).first(), organizace=Organizace.objects.first(), material_originalu=Heslar.objects.filter(nazev_heslare=12).first(), stav=1, ident_cely="XX545461XX2")
    d.save()
    dc = DokumentCast(dokument=d, ident_cely="XX1XX2")
    dc.save()
    na = NeidentAkce(dokument_cast=dc)
    na.save()
    dc.delete()
    na.refresh_from_db()


**delete_related_neident_vedouci**

.. code:: py
    from dokument.models import Dokument, DokumentCast
    from heslar.models import Heslar
    from neidentakce.models import NeidentAkce, NeidentAkceVedouci
    from uzivatel.models import Osoba
    d = Dokument(rada=Heslar.objects.filter(nazev_heslare=26).first(), typ_dokumentu=Heslar.objects.filter(nazev_heslare=35).first(), organizace=Organizace.objects.first(), material_originalu=Heslar.objects.filter(nazev_heslare=12).first(), stav=1, ident_cely=get_random_string())
    d.save()
    dc = DokumentCast(dokument=d, ident_cely=get_random_string())
    dc.save()
    na = NeidentAkce(dokument_cast=dc)
    na.save()
    nav = NeidentAkceVedouci(neident_akce=na, vedouci=Osoba.objects.first())
    nav.save()
    dc.delete()
    nav.refresh_from_db()


**delete_unconfirmed_pian**

.. code:: py
    from heslar.models import Heslar
    from pian.models import Pian
    p_1 = Pian.objects.first()
    p_2 = Pian(presnost=Heslar.objects.filter(nazev_heslare=24).filter(zkratka__lt="4").first(), typ=Heslar.objects.filter(nazev_heslare=40).first(), geom=p_1.geom, ident_cely="A", zm10=p_1.zm10, zm50=p_1.zm50)
    p_2.save()
    dj = DokumentacniJednotka(typ=Heslar.objects.filter(nazev_heslare=34).first(), pian=p_2, archeologicky_zaznam=ArcheologickyZaznam.objects.last())
    dj.save()
    dj.delete()
    p_2.refresh_from_db()
