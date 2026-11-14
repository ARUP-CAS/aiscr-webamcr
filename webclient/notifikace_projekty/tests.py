"""Explicitní testy notifikační úlohy s vlastními referenčními daty."""

from unittest.mock import patch

from core.constants import PROJEKT_STAV_ZAPSANY, ROLE_ARCHEOLOG_ID, ROLE_BADATEL_ID
from core.tests.fedora_fixtures import mock_fedora_for_fixture
from core.tests.notification_fixtures import mock_project_notifications
from cron.tests._import_test_fixtures import (
    create_heslar_fixtures,
    create_organizace,
    create_projekt,
    create_projekt_typ,
    create_ruian_with_pian,
)
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from heslar.models import Heslar, RuianKatastr
from notifikace_projekty import tasks
from notifikace_projekty.models import Pes
from projekt.models import Projekt
from uzivatel.models import User, UserNotificationType


class ProjectNotificationTaskTest(TestCase):
    """Ověřuje skutečný výběr příjemců a dispatch; pouze doručení emailu je mockováno."""

    @classmethod
    @mock_fedora_for_fixture()
    def setUpTestData(cls):
        """Připraví projekt, hlídacího psa a oba typy notifikací nutné pro úlohu."""
        Group.objects.get_or_create(pk=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        group, _ = Group.objects.get_or_create(pk=ROLE_ARCHEOLOG_ID, defaults={"name": "archeolog"})
        heslars = create_heslar_fixtures("notify")
        cls.katastr, _ = create_ruian_with_pian("notify", "P-0003-999001", heslars)
        cls.projekt_typ = create_projekt_typ("notify")
        cls.anonymous_access = Heslar.objects.create(
            ident_cely="HES-NOTIFY-ANON",
            nazev_heslare=heslars["pristupnost"].nazev_heslare,
            heslo="Anonymní",
        )
        with patch("projekt.models.PRISTUPNOST_ANONYM_ID", cls.anonymous_access.pk):
            cls.projekt = create_projekt("C-202699991", cls.katastr, cls.projekt_typ)
        cls.notification, _ = UserNotificationType.objects.get_or_create(ident_cely="E-P-02")
        cls.subscription, _ = UserNotificationType.objects.get_or_create(ident_cely="S-E-P-02a")
        cls.user = User(
            email="notification-test@example.cz",
            ident_cely="U-999091",
            first_name="Notification",
            last_name="Test",
            organizace=create_organizace("notify", heslars),
            is_active=True,
        )
        cls.user.suppress_signal = True
        cls.user.save()
        cls.user.groups.add(group)
        cls.user.notification_types.add(cls.subscription)
        Pes.objects.create(
            user=cls.user,
            content_type=ContentType.objects.get_for_model(RuianKatastr),
            object_id=cls.katastr.pk,
        )

    def setUp(self):
        """Naváže ID projektu z fixture na skutečné mapování typu notifikace."""
        self.enterContext(patch("projekt.models.PRISTUPNOST_ANONYM_ID", self.anonymous_access.pk))
        self.enterContext(
            patch.multiple(
                tasks,
                TYP_PROJEKTU_BADATELSKY_ID=self.projekt_typ.pk,
                TYP_PROJEKTU_PRUZKUM_ID=-20,
                TYP_PROJEKTU_ZACHRANNY_ID=-30,
            )
        )

    def test_explicit_task_selects_subscribed_watchdog_and_calls_mailer(self):
        """Přímý běh úlohy vybere přihlášeného archeologa pro katastr projektu."""
        with patch.object(tasks.Mailer, "send_ep02", return_value="sent") as send:
            self.assertEqual(tasks.check_hlidaci_pes.run(self.projekt.pk), "sent")
        send.assert_called_once()
        recipients, projekt = send.call_args.args
        self.assertEqual(list(recipients.values_list("user_id", flat=True)), [self.user.pk])
        self.assertEqual(projekt, self.projekt)

    def test_explicit_task_does_not_send_without_project_type_subscription(self):
        """Úloha bez odběratele konkrétního typu projektu mailer vůbec nevolá."""
        self.user.notification_types.clear()
        with patch.object(tasks.Mailer, "send_ep02") as send:
            tasks.check_hlidaci_pes.run(self.projekt.pk)
        send.assert_not_called()

    @mock_fedora_for_fixture()
    def test_new_project_dispatches_task_with_saved_primary_key(self):
        """Signál nového projektu předává do delay primární klíč uloženého záznamu."""
        with mock_project_notifications() as dispatch:
            projekt = Projekt(
                ident_cely="C-202699992",
                stav=PROJEKT_STAV_ZAPSANY,
                typ_projektu=self.projekt_typ,
                hlavni_katastr=self.katastr,
            )
            projekt.suppress_signal = True
            projekt.save()
        dispatch.assert_called_once_with(projekt.pk)
