import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone

logger = logging.getLogger(__name__)

# Ident notifikace, která se uživateli odešle poté, co potvrdí svůj email kliknutím
# na aktivační odkaz. Její nejstarší výskyt v logu notifikací považujeme za okamžik potvrzení.
EMAIL_CONFIRMATION_IDENT = "E-U-02"

# Datum zpřístupnění AMČR pro veřejnost. Slouží zároveň jako hranice mezi předmigračními
# a novými účty: účty registrované před tímto datem byly hromadně naimportovány ze staré
# databáze ještě před zavedením logování notifikací, takže u nich potvrzení emailu nelze
# z logu odvodit. Používá se také jako náhradní hodnota potvrzení pro tyto předmigrační účty.
PUBLIC_OPENING_DATE = datetime.datetime(2024, 8, 4)


class Command(BaseCommand):
    """
    Jednorázově zpětně doplní pole ``datum_potvrzeni_emailu`` u uživatelů.

    Postup (tři vzájemně se nepřekrývající množiny účtů bez vyplněného data):

    1. Uživatelům s existující notifikací ``E-U-02`` v logu nastaví datum potvrzení na
       nejstarší výskyt této notifikace (skutečný okamžik potvrzení emailu).
    2. Předmigračním účtům (registrovaným před ``PUBLIC_OPENING_DATE``) bez notifikace
       dosadí statické datum zpřístupnění pro veřejnost.
    3. Aktivním účtům bez notifikace (typicky založené nebo aktivované administrátorem –
       neprošly aktivačním odkazem, ale jsou aktivní, takže je považujeme za potvrzené)
       dosadí datum vzniku účtu (``date_joined``).

    Neaktivní účty bez notifikace zůstanou nevyplněné – to jsou skutečné nepotvrzené
    registrace (kandidáti na likvidaci). Již vyplněná pole se nepřepisují, příkaz je proto
    možné spustit opakovaně.

    Příklady použití::

        python manage.py doplnit_potvrzeni_emailu --dry-run
        python manage.py doplnit_potvrzeni_emailu
    """

    help = "Zpětně doplní datum potvrzení emailu podle logu notifikací (E-U-02), data registrace a aktivity účtu."

    def add_arguments(self, parser):
        """
        Registruje volitelný argument pro zkušební běh bez zápisu do databáze.

        :param parser: Argumentový parser pro přidání nových parametrů příkazu.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Pouze vypíše, kolik záznamů by se změnilo, bez zápisu do databáze.",
        )

    def handle(self, *args, **options):
        """
        Provede zpětné doplnění data potvrzení emailu.

        :param args: Poziční argumenty příkazu (nepoužívá se).
        :param options: Parametr ``options`` slouží jako vstup pro logiku funkce ``handle``.
        """
        from uzivatel.models import NotificationsLog, User

        dry_run = options["dry_run"]

        # ID uživatelů, kterým byla někdy odeslána potvrzovací notifikace.
        log_user_ids = (
            NotificationsLog.objects.filter(
                notification_type__ident_cely=EMAIL_CONFIRMATION_IDENT,
                user__isnull=False,
            )
            .values_list("user_id", flat=True)
            .distinct()
        )

        # Nejstarší výskyt potvrzovací notifikace pro daného uživatele (přes OuterRef na User).
        first_confirmation = (
            NotificationsLog.objects.filter(
                user_id=OuterRef("pk"),
                notification_type__ident_cely=EMAIL_CONFIRMATION_IDENT,
            )
            .order_by("created_at")
            .values("created_at")[:1]
        )

        datum_otevreni = timezone.make_aware(PUBLIC_OPENING_DATE)

        # Tři disjunktní množiny účtů bez data potvrzení – pořadí zpracování se nepřekrývá:
        # 1) mají potvrzovací notifikaci v logu
        qs_z_logu = User.objects.filter(datum_potvrzeni_emailu__isnull=True, pk__in=log_user_ids)
        # 2) předmigrační účty bez notifikace (registrace před zpřístupněním pro veřejnost)
        qs_premigracni = User.objects.filter(
            datum_potvrzeni_emailu__isnull=True,
            date_joined__lt=datum_otevreni,
        ).exclude(pk__in=log_user_ids)
        # 3) aktivní účty bez notifikace, které nejsou předmigrační (vytvořené/aktivované adminem)
        qs_aktivni = User.objects.filter(
            datum_potvrzeni_emailu__isnull=True,
            is_active=True,
            date_joined__gte=datum_otevreni,
        ).exclude(pk__in=log_user_ids)

        pocet_z_logu = qs_z_logu.count()
        pocet_premigracni = qs_premigracni.count()
        pocet_aktivni = qs_aktivni.count()

        self.stdout.write("Zpětné doplnění data potvrzení emailu")
        self.stdout.write(f"  - z logu notifikací ({EMAIL_CONFIRMATION_IDENT}): {pocet_z_logu} účtů")
        self.stdout.write(
            f"  - předmigrační účty (registrace před {datum_otevreni.date()}): {pocet_premigracni} účtů "
            f"-> {datum_otevreni.date()}"
        )
        self.stdout.write(f"  - aktivní účty bez potvrzení (vytvořené adminem): {pocet_aktivni} účtů -> date_joined")

        if dry_run:
            self.stdout.write(self.style.WARNING("Režim --dry-run: žádné změny nebyly zapsány."))
            logger.info(
                "uzivatel.doplnit_potvrzeni_emailu.dry_run",
                extra={"z_logu": pocet_z_logu, "premigracni": pocet_premigracni, "aktivni": pocet_aktivni},
            )
            return

        with transaction.atomic():
            # Skutečná data z logu mají přednost, poté náhradní datumy pro zbylé množiny.
            qs_z_logu.update(datum_potvrzeni_emailu=Subquery(first_confirmation))
            qs_premigracni.update(datum_potvrzeni_emailu=datum_otevreni)
            qs_aktivni.update(datum_potvrzeni_emailu=F("date_joined"))

        zbyva_nevyplneno = User.objects.filter(datum_potvrzeni_emailu__isnull=True).count()
        self.stdout.write(
            self.style.SUCCESS(f"Hotovo. Bez data potvrzení zůstává {zbyva_nevyplneno} účtů (neaktivní bez potvrzení).")
        )
        logger.info(
            "uzivatel.doplnit_potvrzeni_emailu.done",
            extra={
                "z_logu": pocet_z_logu,
                "premigracni": pocet_premigracni,
                "aktivni": pocet_aktivni,
                "zbyva_nevyplneno": zbyva_nevyplneno,
            },
        )
