from unittest.mock import patch

from django.test import TestCase
from heslar import hesla
from heslar.models import Heslar
from projekt.models import Projekt


class TestProjektSignals(TestCase):
    def setUp(self):
        pass

    # TODO fix this test it does not work
    @patch("projekt.signals.create_projekt_vazby")
    def test_create_projekt_vazby(self, mock):
        Projekt(
            stav=0,
            typ_projektu=Heslar.objects.get(id=hesla.PROJEKT_ZACHRANNY_ID),
        ).save()

        # Check that your signal was called.
        self.assertTrue(mock.called)
        # Check that your signal was called only once.
        self.assertEqual(mock.call_count, 1)
