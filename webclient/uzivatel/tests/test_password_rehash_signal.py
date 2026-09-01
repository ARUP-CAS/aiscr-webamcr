"""
Testy potlačení Fedora signálu při přehashování hesla (issue #3251, Django 6).

Django při přihlášení přehashuje heslo uložené zastaralým hasherem: zavolá ``set_password()``,
vynuluje ``_password`` a uloží ``save(update_fields=["password"])``
(``AbstractBaseUser.check_password``). Takové uložení není změnou dat uživatele, takže
``create_ident_cely`` nastaví ``suppress_signal`` a ``user_post_save_method`` přeskočí zápis
metadat do Fedory i rotaci API tokenu.

Testy hlídají obě strany podmínky – rehash se potlačí, ale skutečná změna hesla ani jiná
editace uživatele potlačena být nesmí. Nepotřebují databázi ani běžící Fedoru: přijímače
signálů se volají přímo a jejich okolí (``Token``, ``FedoraTransaction``, odesílání e-mailů)
je nahrazeno mockem.
"""

from unittest import mock

from django.test import SimpleTestCase
from uzivatel.models import User
from uzivatel.signals import create_ident_cely, user_post_save_method


def _existing_user(**kwargs):
    """Vrátí neuloženou instanci ``User`` s ``pk``, aby přijímače nešly do větve pro nový záznam."""
    return User(id=1, ident_cely="U-000001", email="test@example.com", **kwargs)


class CreateIdentCelySuppressTests(SimpleTestCase):
    """Pokrývá nastavení ``suppress_signal`` v ``pre_save`` přijímači ``create_ident_cely``."""

    def _call(self, instance, update_fields):
        """Zavolá ``create_ident_cely`` s daným ``update_fields`` a vrátí ``suppress_signal``."""
        # Při `update_fields=None` si přijímač dohledává původní záznam z databáze.
        with mock.patch.object(User, "objects") as objects:
            objects.filter.return_value.count.return_value = 0
            create_ident_cely(sender=User, instance=instance, update_fields=update_fields)
        return instance.suppress_signal

    def test_rehash_hesla_potlaci_signal(self):
        """Přehashování hesla Djangem (``_password`` je None) signál potlačí."""
        user = _existing_user()
        user.set_password("tajneheslo")
        # Django po `set_password()` `_password` vynuluje, viz `AbstractBaseUser.check_password`.
        user._password = None

        self.assertTrue(self._call(user, update_fields=["password"]))

    def test_skutecna_zmena_hesla_signal_nepotlaci(self):
        """Změna hesla přes ``set_password()`` a ``save()`` bez ``update_fields`` se nepotlačí."""
        user = _existing_user()
        user.set_password("noveheslo")

        self.assertFalse(self._call(user, update_fields=None))

    def test_zmena_hesla_s_update_fields_signal_nepotlaci(self):
        """I s ``update_fields=["password"]`` rozhoduje ``_password`` – vyplněné znamená změnu hesla."""
        user = _existing_user()
        user.set_password("noveheslo")
        self.assertEqual(user._password, "noveheslo")

        self.assertFalse(self._call(user, update_fields=["password"]))

    def test_pouze_last_login_potlaci_signal(self):
        """Zápis samotného ``last_login`` při přihlášení signál potlačí."""
        self.assertTrue(self._call(_existing_user(), update_fields=["last_login"]))

    def test_password_spolu_s_jinym_polem_signal_nepotlaci(self):
        """Uložení ``password`` spolu s dalším polem už není rehash, takže se nepotlačí."""
        user = _existing_user()
        user.set_password("tajneheslo")
        user._password = None

        self.assertFalse(self._call(user, update_fields=["password", "email"]))

    def test_bezna_editace_uzivatele_signal_nepotlaci(self):
        """Běžná editace uživatele (např. e-mailu) se nepotlačuje."""
        self.assertFalse(self._call(_existing_user(), update_fields=["email"]))


class UserPostSaveSuppressTests(SimpleTestCase):
    """Pokrývá, co ``user_post_save_method`` při potlačeném signálu (ne)udělá."""

    def _call(self, suppress_signal):
        """Zavolá ``user_post_save_method`` a vrátí mocky ``Token``, ``FedoraTransaction`` a ``save_metadata``."""
        user = _existing_user(is_active=True)
        user.suppress_signal = suppress_signal
        user.save_metadata = mock.Mock()

        with (
            mock.patch("uzivatel.signals.Token") as token,
            mock.patch("uzivatel.signals.FedoraTransaction") as fedora_transaction,
            mock.patch("uzivatel.signals.send_deactivation_email"),
            mock.patch("uzivatel.signals.send_account_confirmed_email"),
        ):
            user_post_save_method(sender=User, instance=user, created=False, update_fields=["password"])
        return token, fedora_transaction, user.save_metadata

    def test_potlaceny_signal_nezapisuje_do_fedory_ani_nerotuje_token(self):
        """Při rehashi hesla se nesmí zapsat metadata do Fedory ani přegenerovat API token."""
        token, fedora_transaction, save_metadata = self._call(suppress_signal=True)

        save_metadata.assert_not_called()
        token.objects.get.assert_not_called()
        token.objects.create.assert_not_called()
        fedora_transaction.assert_not_called()

    def test_nepotlaceny_signal_zapisuje_do_fedory_a_rotuje_token(self):
        """Skutečná změna uživatele metadata do Fedory zapíše a API token přegeneruje."""
        token, _fedora_transaction, save_metadata = self._call(suppress_signal=False)

        save_metadata.assert_called_once()
        token.objects.create.assert_called_once()
