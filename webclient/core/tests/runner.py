from django.contrib.gis.geos import GEOSGeometry
from django.test.runner import DiscoverRunner as BaseRunner
from heslar import hesla
from heslar.models import Heslar, HeslarNazev, RuianKatastr, RuianKraj, RuianOkres


class AMCRMixinRunner(object):
    def setup_databases(self, *args, **kwargs):
        temp_return = super(AMCRMixinRunner, self).setup_databases(*args, **kwargs)
        print("Setting up my database content ...")

        kraj_praha = RuianKraj(id=84, nazev="Hlavní město Praha", rada_id="C", kod=1)
        kraj_brno = RuianKraj(id=85, nazev="Jihomoravský kraj", rada_id="C", kod=2)
        okres_praha = RuianOkres(
            id=162, nazev="Praha", kraj=kraj_brno, spz="spz", kod=3
        )
        okres_brno_venkov = RuianOkres(
            id=163, nazev="Brno-venkov", kraj=kraj_brno, spz="spz", kod=4
        )
        odrovice = RuianKatastr(
            id=150,
            nazev="ODROVICE",
            okres=okres_brno_venkov,
            kod=3,
            aktualni=True,
            definicni_bod=GEOSGeometry(
                "0101000020E610000042D35729E77F3040234F91EAF9804840"
            ),
            hranice=GEOSGeometry(
                "0106000020E610000001000000010300000001000000130000006E6F8E0B8E84304091B2E4D54"
                "48248401F1E93480586304064D23AA54D814840D3819AAF5E863040D2583431DC804840A29439"
                "0E6F843040DAE2ADDC72804840862715C5D883304025CEA19C628048400FD982CE3D833040E86"
                "8346F5E80484040B173420C7E304018B719A61B8048402B66119F397830409FD10A33C97F4840"
                "92BAF062A4783040827C4FCB55804840FA5C963DC87A3040C3E02EA9E18048408C9A8056D17A3"
                "040B9BFA41AE6804840BD35778B877C304027BB3E2B83814840B088D6301E813040901D47D721"
                "8248409E2B3B911E813040566325BF258248401ED53C6D73813040739AD6F82F8248400816E571"
                "C0813040542C604C13824840178B9F59228230409A127179028248409D0CB7BE598230403D43D"
                "4B3EF8148406E6F8E0B8E84304091B2E4D544824840"
            ),
            pian=1,
        )
        praha = RuianKatastr(
            id=149,
            nazev="JOSEFOV",
            okres=okres_praha,
            kod=3,
            aktualni=True,
            definicni_bod=GEOSGeometry(
                "0101000020E61000006690F8F089D62C40957C231E2F0B4940"
            ),
            hranice=GEOSGeometry(
                "0106000020E61000000100000001030000000100000013000000ED2BF5120ED62C40E95C8F63"
                "BA0B4940A88DBA2A20D62C40D963192CBC0B49401E0BE95D66D62C40BB04E9FBA20B4940A704"
                "40B545D72C408828418EAA0B49408247C41C53D72C400A133A839B0B49408AF95C4B9CD72C40"
                "D57BA3289D0B494099ABFAC0BBD72C406D51FEF38D0B49403722D2C681D72C40EB2E0074880B"
                "4940755B0FEA61D72C40FA0200188F0B4940ACB20F8D08D72C403F7747528D0B49404F3900CC"
                "2BD72C4096DA754B7E0B49407CBCE723C3D62C4032CA4717750B49400CF2773FFAD62C407ADA"
                "B87E5E0B4940119C9C7068D62C40DD0B0A73530B494072CED04595D62C401AEDAE41410B4940"
                "543910F6CCD42C40791DBCDD5B0B49401050ED8531D52C40B711E7EC920B49406E87F5C48AD5"
                "2C40899F4641A90B4940ED2BF5120ED62C40E95C8F63BA0B4940"
            ),
            pian=1,
        )
        kraj_praha.save()
        kraj_brno.save()
        okres_praha.save()
        okres_brno_venkov.save()
        odrovice.save()
        praha.save()

        hn = HeslarNazev(nazev="Typy projektu")
        hp = HeslarNazev(nazev="Presnost")
        ha = HeslarNazev(nazev="heslar_typ_pian")
        hn.save()
        hp.save()
        ha.save()
        h1 = Heslar(id=hesla.PROJEKT_ZACHRANNY_ID, nazev_heslare=hn)
        h2 = Heslar(id=854, nazev_heslare=hp)
        h3 = Heslar(id=1122, nazev_heslare=ha)
        h1.save()
        h2.save()
        h3.save()

        return temp_return

    def teardown_databases(self, *args, **kwargs):
        # do somthing
        return super(AMCRMixinRunner, self).teardown_databases(*args, **kwargs)


class AMCRTestRunner(AMCRMixinRunner, BaseRunner):
    pass
