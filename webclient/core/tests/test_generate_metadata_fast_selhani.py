"""
Testy účtování selhání v ``generate_metadata_fast``.

Všechna tři místa tady mají společné to, že se dřív tvářila jako úspěch, i když se
záznam do Fedory nedostal - a u 24hodinového běhu nad statisíci záznamů je tichý
neúspěch horší než pád (review PR #4262):

- záznam bez ``ident_cely`` se jen zalogoval a přeskočil; do ``failures`` se nedostal
  a ``_zkontroluj_konzistenci`` prázdné identy odfiltrovává na obou stranách, takže
  chybějící záznam nikdo neohlásil a běh skončil nulovým exit kódem,
- souvislá série selhání (Fedora dole) běh nezastavila - každý záznam vyčerpal
  ``_RECORD_TIME_BUDGET`` a běh se vlekl dál, až ho zvenčí někdo zabil,
- placeholder neodpovídající manifestu byl jen WARNING a poškozené bajty se do Fedory
  zapsaly nevratně.
"""

import hashlib
import io
import json
import os
import tempfile
from types import SimpleNamespace

from core.management.commands.generate_metadata_fast import (
    _PLACEHOLDER_MANIFEST_PATH,
    _dokud_pojistka_drzi,
    _load_placeholders,
    _Pojistka,
)
from django.core.management.base import BaseCommand
from django.test import SimpleTestCase
from PIL import Image


class PojistkaTest(SimpleTestCase):
    """Chování ``_Pojistka`` - pojistky proti souvislé sérii selhání."""

    def test_spusti_se_az_na_limitu(self):
        """Pojistka se spustí přesně na zadaném počtu selhání po sobě, ne dřív."""
        pojistka = _Pojistka(3)
        self.assertFalse(pojistka.selhani())
        self.assertFalse(pojistka.selhani())
        self.assertFalse(pojistka.spustena)
        self.assertTrue(pojistka.selhani())
        self.assertTrue(pojistka.spustena)

    def test_uspech_nuluje_serii(self):
        """
        Roztroušená selhání pojistku nespustí.

        Tohle je celý smysl "po sobě": vadná data jednotlivých záznamů běh zastavit
        nesmí, zastavit ho smí až systémový problém.
        """
        pojistka = _Pojistka(3)
        for _ in range(100):
            pojistka.selhani()
            pojistka.selhani()
            pojistka.uspech()
        self.assertFalse(pojistka.spustena)
        self.assertEqual(pojistka.vrchol, 2)

    def test_nulovy_limit_pojistku_vypina(self):
        """``--max-selhani-po-sobe 0`` znamená "nehlídej", ne "spusť se hned"."""
        pojistka = _Pojistka(0)
        for _ in range(1000):
            self.assertFalse(pojistka.selhani())
        self.assertFalse(pojistka.spustena)
        self.assertEqual(pojistka.vrchol, 1000)

    def test_dokud_pojistka_drzi_prestane_dodavat_praci(self):
        """Po spuštění pojistky se ze zdroje položek nesmí vzít nic dalšího."""
        pojistka = _Pojistka(2)
        odebrane = []

        def zdroj():
            for i in range(100):
                odebrane.append(i)
                yield i

        zpracovane = []
        for polozka in _dokud_pojistka_drzi(zdroj(), pojistka):
            zpracovane.append(polozka)
            pojistka.selhani()

        self.assertEqual(zpracovane, [0, 1])
        # Generátor smí mít o jednu položku napřed (vytáhne ji a teprve pak zjistí, že
        # pojistka spadla), ale rozhodně nesmí projít zbytek querysetu.
        self.assertLessEqual(len(odebrane), 3)

    def test_bez_pojistky_se_nic_neomezuje(self):
        """``None`` místo pojistky (výchozí stav ``_process_record``) nesmí nic filtrovat."""
        self.assertEqual(list(_dokud_pojistka_drzi(range(5), None)), [0, 1, 2, 3, 4])


class ChybejiciIdentTest(SimpleTestCase):
    """Záznam bez ``ident_cely`` se musí započítat jako selhání, ne jako přeskočení."""

    def test_zaznam_bez_identu_jde_do_failures_i_do_pojistky(self):
        """
        Bez ``ident_cely`` nejde záznam ve Fedoře pojmenovat, takže se nezapíše.

        Musí se objevit ve ``failures`` (odtud roste ``_pocet_selhani`` a nenulový exit
        kód) a nahlásit pojistce - jinak by celý model bez identů proběhl jako úspěch.
        """
        from core.management.commands.generate_metadata_fast import Command

        failures = []
        pojistka = _Pojistka(2)
        obj = SimpleNamespace(pk=42, ident_cely="")

        Command._process_record(obj, writer=None, max_retries=0, failures=failures, pojistka=pojistka)

        self.assertEqual(len(failures), 1)
        pk, ident, popis = failures[0]
        self.assertEqual(pk, 42)
        self.assertEqual(ident, "")
        self.assertIn("ident_cely", popis)
        self.assertFalse(pojistka.spustena, "jeden takový záznam pojistku spustit nemá")

        Command._process_record(obj, writer=None, max_retries=0, failures=failures, pojistka=pojistka)
        self.assertEqual(len(failures), 2)
        self.assertTrue(pojistka.spustena, "série záznamů bez identu už pojistku spustit má")

    def test_spustena_pojistka_zastavi_dalsi_praci(self):
        """Po spuštění pojistky už ``_process_record`` nesmí nic dělat ani hlásit."""
        from core.management.commands.generate_metadata_fast import Command

        failures = []
        pojistka = _Pojistka(1)
        pojistka.selhani()
        self.assertTrue(pojistka.spustena)

        Command._process_record(
            SimpleNamespace(pk=1, ident_cely=""), writer=None, max_retries=0, failures=failures, pojistka=pojistka
        )
        self.assertEqual(failures, [])

    def test_command_ma_volbu_max_selhani_po_sobe(self):
        """Volba musí být v parseru, být ve výchozím stavu zapnutá a jít vypnout nulou."""
        from core.management.commands.generate_metadata_fast import Command

        parser = Command().create_parser("manage.py", "generate_metadata_fast")
        vychozi = parser.parse_args([]).max_selhani_po_sobe
        self.assertIsInstance(vychozi, int)
        self.assertGreater(vychozi, 0, "pojistka musí být ve výchozím stavu zapnutá")
        self.assertEqual(parser.parse_args(["--max-selhani-po-sobe", "0"]).max_selhani_po_sobe, 0)
        self.assertIsInstance(Command(), BaseCommand)


class PlaceholderHashTest(SimpleTestCase):
    """Placeholder neodpovídající manifestu musí načtení zastavit, ne jen zalogovat."""

    @staticmethod
    def _manifest(adresar, obsah, hash512):
        """
        Vytvoří minimální manifest s jedním placeholderem.

        :param adresar: Adresář, do kterého se zapíše manifest i placeholder.
        :param obsah: Bajty placeholderu.
        :param hash512: SHA-512, které se zapíše do manifestu.
        :return: Cesta k manifestu.
        """
        with open(os.path.join(adresar, "p.bin"), "wb") as handle:
            handle.write(obsah)
        cesta = os.path.join(adresar, "manifest.json")
        with io.open(cesta, "w", encoding="utf-8") as handle:
            json.dump({"application/octet-stream": {"file": "p.bin", "sha512": hash512, "size": len(obsah)}}, handle)
        return cesta

    def test_shodny_hash_projde(self):
        """Kontrolní případ - správný manifest se načte a vrátí dopočítaný hash."""
        obsah = b"abc"
        with tempfile.TemporaryDirectory() as adresar:
            cesta = self._manifest(adresar, obsah, hashlib.sha512(obsah).hexdigest())
            nactene = _load_placeholders(cesta)
        self.assertEqual(nactene["application/octet-stream"]["orig_bytes"], obsah)
        self.assertEqual(nactene["application/octet-stream"]["orig_sha512"], hashlib.sha512(obsah).hexdigest())

    def test_neshoda_hashe_vyhodi_valueerror(self):
        """
        Neshoda musí vyhodit ``ValueError``.

        Na ten je navázané ``except (OSError, ValueError, KeyError)`` v ``handle``, které
        z něj udělá ``CommandError`` - běh tedy skončí dřív, než se do Fedory cokoli zapíše.
        """
        with tempfile.TemporaryDirectory() as adresar:
            cesta = self._manifest(adresar, b"abc", "0" * 128)
            with self.assertRaises(ValueError) as chyceno:
                _load_placeholders(cesta)
        self.assertIn("p.bin", str(chyceno.exception))

    def test_rozmery_nahledu_odpovidaji_generatoru_aplikace(self):
        """
        Náhledy obrázkových placeholderů musí mít rozměry, jaké by dala sama aplikace.

        ``FedoraRepositoryConnector.__generate_thumb`` volá ``Image.thumbnail((100,100))``,
        resp. ``((800,800))``, a ``thumbnail`` obrázek **nikdy nezvětšuje**. U placeholderu,
        který je menší než cílový rozměr, proto oba náhledy vyjdou stejně - a je to
        správně, ne chyba manifestu: ``image/bmp`` má originál 100x100, takže jeho
        ``thumb`` i ``thumb_large`` jsou tentýž obrázek, zatímco ostatní rastry mají
        originál 300x300 a velký náhled se od malého liší. Očekávané rozměry se tu proto
        počítají týmž ``thumbnail()``, ne ručně (review PR #4262).

        Těch 100x100 u ``image/bmp`` je **záměr, ne opomenutí**: BMP se neukládá
        komprimovaně, takže 300x300 jako u ostatních rastrů by dělalo 270 kB místo
        30 kB - a to na každém souboru toho typu ve Fedoře. Nezvětšovat (review PR #4262).
        """
        base_dir = os.path.dirname(_PLACEHOLDER_MANIFEST_PATH)
        with io.open(_PLACEHOLDER_MANIFEST_PATH, encoding="utf-8") as handle:
            manifest = json.load(handle)

        zkontrolovano = 0
        for mimetype, polozka in manifest.items():
            if not mimetype.startswith("image/"):
                continue
            try:
                original = Image.open(os.path.join(base_dir, polozka["file"]))
                original.load()
            except Exception:
                continue  # formát, který Pillow neotevře (např. svg) - náhled se dělá z ikony
            for klic, max_rozmer in (("thumb", 100), ("thumb_large", 800)):
                nahled = polozka.get(klic)
                if not nahled:
                    continue
                ocekavany = original.copy()
                ocekavany.thumbnail((max_rozmer, max_rozmer))
                skutecny = Image.open(os.path.join(base_dir, nahled["file"]))
                self.assertEqual(
                    skutecny.size,
                    ocekavany.size,
                    f"{mimetype} {klic}: originál {original.size}, čekáno {ocekavany.size}, "
                    f"v manifestu {skutecny.size}",
                )
                zkontrolovano += 1
        self.assertGreaterEqual(zkontrolovano, 8, "zkontrolovalo se podezřele málo náhledů")

    def test_dodavany_manifest_sedi_na_bajty_placeholderu(self):
        """
        Manifest v repozitáři musí sedět na soubory vedle sebe.

        Kdyby ne, ostrý běh by po předchozím testu skončil ``CommandError`` hned na
        startu. V issue #3967 se přesně tohle stalo (CRLF poškozené bajty v manifestu),
        proto se to hlídá testem, ne jen během.
        """
        placeholdery = _load_placeholders()
        self.assertGreater(len(placeholdery), 0)
        for mimetype, polozka in placeholdery.items():
            self.assertTrue(polozka["orig_bytes"], f"prázdný placeholder pro {mimetype}")
