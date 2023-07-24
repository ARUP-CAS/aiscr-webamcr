from typing import Final
from django.utils.translation import gettext_lazy as _

FORM_NOT_VALID: Final = "Forma není validní."

PRISTUP_ZAKAZAN: Final = "common.message.pristupZakazan.text"

ZAZNAM_USPESNE_VYTVOREN: Final = "Záznam byl úspěšně vytvořen."
ZAZNAM_SE_NEPOVEDLO_VYTVORIT: Final = "Záznam se nepovedlo vytvořit."
ZAZNAM_USPESNE_EDITOVAN: Final = "Záznam byl úspěšně upraven."
ZAZNAM_SE_NEPOVEDLO_EDITOVAT: Final = "Záznam se nepovedlo editovat."
ZAZNAM_USPESNE_SMAZAN: Final = "Záznam byl úspěšně smazán."
ZAZNAM_SE_NEPOVEDLO_SMAZAT: Final = "Záznam nebyl smazán."
ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY: Final = "Záznam nebyl smazán kvůli navázaným záznamům."
MAXIMUM_IDENT_DOSAZEN: Final = "Byl překročen limit při přidělování identifikátoru. Pro vyřešení problému kontaktujte administrátora AMČR."
MAXIMUM_AKCII_DOSAZENO: Final = "Byl překročen limit akcií pro jeden projekt."
MAXIMUM_DJ_DOSAZENO: Final = (
    "Byl překročen limit dokumentačních jednotek pro jednu akci."
)
MAXIMUM_KOMPONENT_DOSAZENO: Final = (
    "Byl překročen limit komponent pro dokumentační jednotky."
)

# Projekt
PROJEKT_USPESNE_PRIHLASEN: Final = "Projekt byl úspěšně přihlášen."
PROJEKT_USPESNE_VRACEN: Final = "Projekt byl úspěšně vrácen do předchozího stavu."
PROJEKT_USPESNE_SCHVALEN: Final = "Projekt byl úspěšně schválen."
PROJEKT_USPESNE_ZAHAJEN_V_TERENU: Final = "Projekt byl úspěšně zahájen v terénu."
PROJEKT_USPESNE_UKONCEN_V_TERENU: Final = "Projekt byl úspěšně ukončen v terénu."
PROJEKT_USPESNE_UZAVREN: Final = "Projekt byl úspěšně uzavřen."
PROJEKT_USPESNE_ZRUSEN: Final = "Projekt byl úspěšně zrušen."
PROJEKT_USPESNE_ARCHIVOVAN: Final = "Projekt byl úspěšně archivován."
PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI: Final = "Projekt byl úspěšně navržen ke zrušení."
PROJEKT_NELZE_UZAVRIT: Final = (
    "Projekt nelze uzavřít. Zkontrolujte zda má všechny náležitosti."
)
PROJEKT_NELZE_ARCHIVOVAT: Final = (
    "Projekt nelze archivovat. Zkontrolujte zda má všechny náležitosti."
)
PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI: Final = (
    "Projekt nelze navrhnout ke zrušení. Nesmí mít žádné akce."
)
PROJEKT_NELZE_SMAZAT: Final = "Projekt nelze smazat."
PROJEKT_NEKDO_ZMENIL_STAV: Final = _("core.message_constants.projektZmenaStavuNekymJinym.text")

AKCE_USPESNE_ZAPSANA: Final = "Akce úspěšně zapsána."
AKCE_USPESNE_ODESLANA: Final = "Akce úspěšně odeslána."
AKCE_USPESNE_ARCHIVOVANA: Final = "Akce úspěšně archivovaná."
AKCE_USPESNE_VRACENA: Final = "Akce úspěšně vrácena."
AKCE_NELZE_ODESLAT: Final = "Akci nelze odeslat."
AKCE_NELZE_ARCHIVOVAT: Final = "Akci nelze archivovat."
AKCE_NEKDO_ZMENIL_STAV: Final = _("core.message_constants.akceZmenaStavuNekymJinym.text")

DOKUMENT_USPESNE_ODESLAN: Final = "Dokument úspěšně odeslán."
DOKUMENT_USPESNE_ARCHIVOVAN: Final = "Dokument úspěšně archivován."
DOKUMENT_USPESNE_VRACEN: Final = "Dokument úspěšně vrácen."
DOKUMENT_NELZE_ODESLAT: Final = "Dokument nelze odeslat."
DOKUMENT_NELZE_ARCHIVOVAT: Final = "Dokument nelze archivovat."
DOKUMENT_NELZE_ARCHIVOVAT_CHYBY_SOUBOR: Final = _(
    "core.message_constants.dokumentNelzeArchivovatChybaSouboru.text"
)
DOKUMENT_USPESNE_PRIPOJEN: Final = "Dokument úspěšně připojen."
DOKUMENT_JIZ_BYL_PRIPOJEN: Final = "Dokument již byl připojen!"
DOKUMENT_USPESNE_ODPOJEN: Final = "Dokument úspěšně odpojen."
VYBERTE_PROSIM_POLOHU: Final = "Vyberte prosím lokalizaci na mapě."
DOKUMENT_NEKDO_ZMENIL_STAV: Final = _("core.message_constants.dokumentZmenaStavuNekymJinym.text")
DOKUMENT_ODPOJ_ZADNE_RELACE: Final = _("core.message_constants.dokumentOdpojitDokumentBezRelace.text")
DOKUMENT_ODPOJ_ZADNE_RELACE_MEZI_DOK_A_ZAZNAM: Final = _(
    "core.message_constants.dokumentOdpojitDokumentBezRelaceMeziZaznamemDokumentem.text"
)
DOKUMENT_AZ_USPESNE_PRIPOJEN: Final = _("core.message_constants.dokumentArchzUspesnePripojen.text")
DOKUMENT_PROJEKT_USPESNE_PRIPOJEN: Final = _(
    "core.message_constants.dokumentProjektUspesnePripojen.text"
)
DOKUMENT_CAST_USPESNE_ODPOJEN: Final = _("core.message_constants.dokumentCastUspesneOdpojena.text")
DOKUMENT_CAST_USPESNE_SMAZANA: Final = _("core.message_constants.dokumentCastUspesneSmazana.text")
DOKUMENT_NEIDENT_AKCE_USPESNE_SMAZANA: Final = _(
    "core.message_constants.dokumentNeidentAkceUspesneSmazana.text"
)
# Osoba
OSOBA_USPESNE_PRIDANA: Final = "Osoba úspěšně přidána."
OSOBA_JIZ_EXISTUJE: Final = "Jméno již existuje."

# Pian
PIAN_USPESNE_ODPOJEN: Final = "Pian uspesne odpojen."
PIAN_USPESNE_POTVRZEN: Final = "Pian uspesne potvrzen."
PIAN_USPESNE_SMAZAN: Final = "Pian byl smazán."
PIAN_NEVALIDNI_GEOMETRIE: Final = "Pian má nevalidní geometrii."
PIAN_VALIDACE_VYPNUTA: Final = "Geometrii Pianu se nepodařilo ověřit."

# SN
SAMOSTATNY_NALEZ_VRACEN: Final = "Samostatný nález vrácen do předchozího stavu."
SAMOSTATNY_NALEZ_NELZE_ODESLAT: Final = "Samostatný nález nelze odeslat."
SAMOSTATNY_NALEZ_ODESLAN: Final = "Samostatný nález úspěšně odeslán."
SAMOSTATNY_NALEZ_POTVRZEN: Final = "Samostatný nález úspěšně potvrzen."
SAMOSTATNY_NALEZ_ARCHIVOVAN: Final = "Samostatný nález úspěšně archivován."
SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV: Final = _("core.message_constants.pasZmenaStavuNekymJinym.text")

# Spoluprace
ZADOST_O_SPOLUPRACI_VYTVORENA: Final = "Žádost o spolupráci byla vytvořena."
SPOLUPRACE_BYLA_AKTIVOVANA: Final = "Spolupráce byla aktivována."
SPOLUPRACE_BYLA_DEAKTIVOVANA: Final = "Spolupráce byla deaktivována."
SPOLUPRACI_NELZE_AKTIVOVAT: Final = "Spolupráci nejde aktivovat."
SPOLUPRACI_NELZE_DEAKTIVOVAT: Final = "Spolupráci nejde deaktivovat."

# Auto-logout
AUTOLOGOUT_AFTER_LOGOUT: Final = _("core.message_constants.autologoutAfterlogout.text")
AUTOLOGOUT_EXPIRATION_WARNING: Final = _("core.message_constants.autologoutExpirationwarning.text")
AUTOLOGOUT_REFRESH_ERROR: Final = _("core.message_constants.autologoutRefresherror.text")
AUTOLOGOUT_REFRESH_SUCCESS: Final = _("core.message_constants.autologoutRefreshsuccess.text")
MAINTENANCE_LOGOUT_WARNING: Final = _("core.message_constants.maintenanceLogoutWarning_text")
MAINTENANCE_AFTER_LOGOUT: Final = _("core.message_constants.maintenanceAfterlogout_text")

# DropZone upload messages
UPLOADFILE_REJECTED_PAS: Final = _("core.message_constants.uploadFile.rejectedPas.text")
UPLOADFILE_REJECTED_DOKUMENT: Final = _("core.message_constants.uploadFile.rejectedDokument.text")
UPLOADFILE_REJECTED_ALL: Final = _("core.message_constants.uploadFile.rejectedAll.text")
UPLOADFILE_ERROR: Final = _("core.message_constants.uploadFile.error.text")

# Validation
VALIDATION_NOT_VALID: Final = "Geometrie není validní."
VALIDATION_EMPTY: Final = "Geometrie je prázdná."
VALIDATION_NOT_SIMPLE: Final = "Geometrie není typu simple geometry."
VALIDATION_NOT_MULTIPART: Final = "Geometrie je multigeometrií."
VALIDATION_LINE_LENGTH: Final = "Vzdálenost bodů je nižší než povolená mez."

# Lokalita
LOKALITA_USPESNE_ZAPSANA: Final = _("core.message_constants.lokalitaUspesneZapsana.text")
LOKALITA_USPESNE_ODESLANA: Final = _("core.message_constants.lokalitaUspesneOdeslana.text")
LOKALITA_USPESNE_ARCHIVOVANA: Final = _("core.message_constants.lokalitaUspesneArchivovana.text")
LOKALITA_USPESNE_VRACENA: Final = _("core.message_constants.lokalitaUspesneVracena.text")
LOKALITA_NELZE_ODESLAT: Final = _("core.message_constants.lokalitaNelzeOdeslat.text")
LOKALITA_NELZE_ARCHIVOVAT: Final = _("core.message_constants.lokalitaNelzeArchivovat.text")
LOKALITA_NEKDO_ZMENIL_STAV: Final = _("core.message_constants.lokalitaZmenaStavuNekymJinym.text")

# Externi zdroj
EZ_USPESNE_ZAPSAN: Final = _("core.message_constants.externiZdrojUspesneZapsan.text")
EZ_USPESNE_ODESLAN: Final = _("core.message_constants.externiZdrojUspesneOdeslan.text")
EZ_USPESNE_POTVRZEN: Final = _("core.message_constants.externiZdrojUspesnePotvrzen.text")
EZ_USPESNE_VRACENA: Final = _("core.message_constants.externiZdrojUspesneVracen.text")
EO_USPESNE_ODPOJEN: Final = _("core.message_constants.externiZdrojUspesneOdpojenEO.text")
AKCE_EO_USPESNE_PRIPOJEN: Final = _("core.message_constants.externiZdrojUspesnePripojenaAkceEO.text")
LOKALITA_EO_USPESNE_PRIPOJEN: Final = _(
    "core.message_constants.externiZdrojUspesnePripojenaLokalitaEO.text"
)
AKCE_EO_USPESNE_ODPOJEN: Final = _("core.message_constants.akceUspesneOdpojenEO.text")
LOKALITA_EO_USPESNE_ODPOJEN: Final = _("core.message_constants.lokalitaUspesneOdpojenEO.text")

# Watchdog
HLIDACI_PES_USPESNE_VYTVOREN: Final = _("core.message_constants.notifikaceProjektyUspesneVytvoren.text")
HLIDACI_PES_USPESNE_SMAZAN: Final = _("core.message_constants.notifikaceProjektyUspesneSmazan.text")
HLIDACI_PES_NEUSPESNE_VYTVOREN: Final = _("core.message_constants.notifikaceProjektyNeUspesneVytvoren.text")
HLIDACI_PES_NEUSPESNE_SMAZAN: Final = _("core.message_constants.notifikaceProjektyNeUspesneSmazan.text")
