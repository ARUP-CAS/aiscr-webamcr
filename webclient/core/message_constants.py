from typing import Final
from django.utils.translation import gettext_lazy as _

FORM_NOT_VALID: Final = _("common.message.FORM_NOT_VALID.text")  # Forma není validní.

PRISTUP_ZAKAZAN: Final = _("common.message.pristupZakazan.text")

ZAZNAM_NELZE_SMAZAT_FEDORA = _("common.message.ZAZNAM_NELZE_SMAZAT_FEDORA.text")  # Záznam nelze smazat, protože nebylo dokončeno nahrávání do Fedory..
ZAZNAM_USPESNE_VYTVOREN: Final = _("common.message.ZAZNAM_USPESNE_VYTVOREN.text")  # Záznam byl úspěšně vytvořen.
ZAZNAM_SE_NEPOVEDLO_VYTVORIT: Final = _("common.message.ZAZNAM_SE_NEPOVEDLO_VYTVORIT.text")  # Záznam se nepovedlo vytvořit.
ZAZNAM_USPESNE_EDITOVAN: Final = _("common.message.ZAZNAM_USPESNE_EDITOVAN.text")  # Záznam byl úspěšně upraven.
ZAZNAM_SE_NEPOVEDLO_EDITOVAT: Final = _("common.message.ZAZNAM_SE_NEPOVEDLO_EDITOVAT.text")  # Záznam se nepovedlo editovat.
ZAZNAM_USPESNE_SMAZAN: Final = _("common.message.ZAZNAM_USPESNE_SMAZAN.text")  # Záznam byl úspěšně smazán.
ZAZNAM_SE_NEPOVEDLO_SMAZAT: Final = _("common.message.ZAZNAM_SE_NEPOVEDLO_SMAZAT.text")  # Záznam nebyl smazán.
ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY: Final = _("common.message.ZAZNAM_SE_NEPOVEDLO_SMAZAT_NAVAZANE_ZAZNAMY.text")  # Záznam nebyl smazán kvůli navázaným záznamům.
MAXIMUM_IDENT_DOSAZEN: Final = _("common.message.MAXIMUM_IDENT_DOSAZEN.text")  # Byl překročen limit při přidělování identifikátoru. Pro vyřešení problému kontaktujte administrátora AMČR.
MAXIMUM_AKCII_DOSAZENO: Final = _("common.message.MAXIMUM_AKCI_DOSAZENO.text")  # Byl překročen limit akcí pro jeden projekt.
MAXIMUM_DJ_DOSAZENO: Final = _("common.message.MAXIMUM_DJ_DOSAZENO.text")  # Byl překročen limit dokumentačních jednotek pro jednu akci.
MAXIMUM_KOMPONENT_DOSAZENO: Final = _("common.message.MAXIMUM_KOMPONENT_DOSAZENO.text")  # Byl překročen limit komponent pro dokumentační jednotky.
SPATNY_ZAZNAM_ZAZNAM_VAZBA: Final = _("common.message.SPATNY_ZAZNAM_ZAZNAM_VAZBA.text")
SPATNY_ZAZNAM_SOUBOR_VAZBA: Final = _("common.message.SPATNY_ZAZNAM_SOUBOR_VAZBA.text")

# Projekt
PROJEKT_USPESNE_PRIHLASEN: Final = _("common.message.PROJEKT_USPESNE_PRIHLASEN.text")  # Projekt byl úspěšně přihlášen.
PROJEKT_USPESNE_VRACEN: Final = _("common.message.PROJEKT_USPESNE_VRACEN.text")  # Projekt byl úspěšně vrácen do předchozího stavu.
PROJEKT_USPESNE_SCHVALEN: Final = _("common.message.PROJEKT_USPESNE_SCHVALEN.text")  # Projekt byl úspěšně schválen.
PROJEKT_USPESNE_ZAHAJEN_V_TERENU: Final = _("common.message.PROJEKT_USPESNE_ZAHAJEN_V_TERENU.text")  # Projekt byl úspěšně zahájen v terénu.
PROJEKT_USPESNE_UKONCEN_V_TERENU: Final = _("common.message.PROJEKT_USPESNE_UKONCEN_V_TERENU.text")  # Projekt byl úspěšně ukončen v terénu.
PROJEKT_USPESNE_UZAVREN: Final = _("common.message.PROJEKT_USPESNE_UZAVREN.text")  # Projekt byl úspěšně uzavřen.
PROJEKT_USPESNE_ZRUSEN: Final = _("common.message.PROJEKT_USPESNE_ZRUSEN.text")  # Projekt byl úspěšně zrušen.
PROJEKT_USPESNE_ARCHIVOVAN: Final = _("common.message.PROJEKT_USPESNE_ARCHIVOVAN.text")  # Projekt byl úspěšně archivován.
PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI: Final = _("common.message.PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI.text")  # Projekt byl úspěšně navržen ke zrušení.
PROJEKT_NELZE_UZAVRIT: Final = _("common.message.PROJEKT_NELZE_UZAVRIT.text")  # Projekt nelze uzavřít. Zkontrolujte zda má všechny náležitosti.
PROJEKT_NELZE_ARCHIVOVAT: Final = _("common.message.PROJEKT_NELZE_ARCHIVOVAT.text")  # Projekt nelze archivovat. Zkontrolujte zda má všechny náležitosti.
PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI: Final = _("common.message.PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI.text")  # Projekt nelze navrhnout ke zrušení. Nesmí mít žádné akce.
PROJEKT_NELZE_ZAHAJIT_V_TERENU: Final = _("common.message.PROJEKT_NELZE_ZAHAJIT_V_TERENU.text")  # Projekt nelze zahájit v terénu.

PROJEKT_NELZE_SMAZAT: Final = _("common.message.PROJEKT_NELZE_SMAZAT.text")  # Projekt nelze smazat.
PROJEKT_NEKDO_ZMENIL_STAV: Final = _("core.message_constants.projektZmenaStavuNekymJinym.text")
PROJEKT_NENI_TYP_PRUZKUMNY: Final = _("common.message.PROJEKT_NENI_TYP_PRUZKUMNY.text")
PROJEKT_NENI_TYP_ZACHRANNY: Final = _("common.message.PROJEKT_NENI_TYP_ZACHRANNY.text")

AKCE_USPESNE_ZAPSANA: Final = _("common.message.AKCE_USPESNE_ZAPSANA.text")  # Akce úspěšně zapsána.
AKCE_USPESNE_ODESLANA: Final = _("common.message.AKCE_USPESNE_ODESLANA.text")  # Akce úspěšně odeslána.
AKCE_USPESNE_ARCHIVOVANA: Final = _("common.message.AKCE_USPESNE_ARCHIVOVANA.text")  # Akce úspěšně archivovaná.
AKCE_USPESNE_VRACENA: Final = _("common.message.AKCE_USPESNE_VRACENA.text")  # Akce úspěšně vrácena.
AKCE_NELZE_ODESLAT: Final = _("common.message.AKCE_NELZE_ODESLAT.text")  # Akci nelze odeslat.
AKCE_NELZE_ARCHIVOVAT: Final = _("common.message.AKCE_NELZE_ARCHIVOVAT.text")  # Akci nelze archivovat.
AKCE_NEKDO_ZMENIL_STAV: Final = _("core.message_constants.akceZmenaStavuNekymJinym.text")

DOKUMENT_USPESNE_ODESLAN: Final = _("common.message.DOKUMENT_USPESNE_ODESLAN.text")  # Dokument úspěšně odeslán.
DOKUMENT_USPESNE_ARCHIVOVAN: Final = _("common.message.DOKUMENT_USPESNE_ARCHIVOVAN.text")  # Dokument úspěšně archivován.
DOKUMENT_USPESNE_VRACEN: Final = _("common.message.DOKUMENT_USPESNE_VRACEN.text")  # Dokument úspěšně vrácen.
DOKUMENT_NELZE_ODESLAT: Final = _("common.message.DOKUMENT_NELZE_ODESLAT.text")  # Dokument nelze odeslat.
DOKUMENT_NELZE_ARCHIVOVAT: Final = _("common.message.DOKUMENT_NELZE_ARCHIVOVAT.text")  # Dokument nelze archivovat.
DOKUMENT_NELZE_ARCHIVOVAT_CHYBY_SOUBOR: Final = _("core.message_constants.dokumentNelzeArchivovatChybaSouboru.text")
DOKUMENT_USPESNE_PRIPOJEN: Final = _("common.message.DOKUMENT_USPESNE_PRIPOJEN.text")  # Dokument úspěšně připojen.
DOKUMENT_JIZ_BYL_PRIPOJEN: Final = _("common.message.DOKUMENT_JIZ_BYL_PRIPOJEN.text")  # Dokument již byl připojen!
DOKUMENT_USPESNE_ODPOJEN: Final = _("common.message.DOKUMENT_USPESNE_ODPOJEN.text")  # Dokument úspěšně odpojen.
VYBERTE_PROSIM_POLOHU: Final = _("common.message.VYBERTE_PROSIM_POLOHU.text")  # Vyberte prosím lokalizaci na mapě.
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
OSOBA_USPESNE_PRIDANA: Final = _("common.message.OSOBA_USPESNE_PRIDANA.text")  # Osoba úspěšně přidána.
OSOBA_JIZ_EXISTUJE: Final = _("common.message.OSOBA_JIZ_EXISTUJE.text")  # Jméno již existuje.

# PIAN
PIAN_USPESNE_ODPOJEN: Final = _("common.message.PIAN_USPESNE_ODPOJEN.text")  # Pian uspesne odpojen.
PIAN_USPESNE_POTVRZEN: Final = _("common.message.PIAN_USPESNE_POTVRZEN.text")  # Pian uspesne potvrzen.
PIAN_USPESNE_SMAZAN: Final = _("common.message.PIAN_USPESNE_SMAZAN.text")  # Pian byl smazán.
PIAN_NEVALIDNI_GEOMETRIE: Final = _("common.message.PIAN_NEVALIDNI_GEOMETRIE.text")  # Pian má nevalidní geometrii.
PIAN_VALIDACE_VYPNUTA: Final = _("common.message.PIAN_VALIDACE_VYPNUTA.text")  # Geometrii Pianu se nepodařilo ověřit.

# SN
SAMOSTATNY_NALEZ_VRACEN: Final = _("common.message.SAMOSTATNY_NALEZ_VRACEN.text")  # Samostatný nález vrácen do předchozího stavu.
SAMOSTATNY_NALEZ_NELZE_ODESLAT: Final = _("common.message.SAMOSTATNY_NALEZ_NELZE_ODESLAT.text")  # Samostatný nález nelze odeslat.
SAMOSTATNY_NALEZ_ODESLAN: Final = _("common.message.SAMOSTATNY_NALEZ_ODESLAN.text")  # Samostatný nález úspěšně odeslán.
SAMOSTATNY_NALEZ_POTVRZEN: Final = _("common.message.SAMOSTATNY_NALEZ_POTVRZEN.text")  # Samostatný nález úspěšně potvrzen.
SAMOSTATNY_NALEZ_NELZE_POTVRDIT: Final = _("common.message.SAMOSTATNY_NALEZ_NELZE_POTVRDIT.text")  # Samostatný nález nelze potvrdit.
SAMOSTATNY_NALEZ_ARCHIVOVAN: Final = _("common.message.SAMOSTATNY_NALEZ_ARCHIVOVAN.text")  # Samostatný nález úspěšně archivován.
SAMOSTATNY_NALEZ_NELZE_ARCHIVOVAT: Final = _("common.message.SAMOSTATNY_NALEZ_NELZE_ARCHIVOVAT.text")  # Samostatný nález nelze archivovat.
SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV: Final = _("core.message_constants.pasZmenaStavuNekymJinym.text")

# Spoluprace
ZADOST_O_SPOLUPRACI_VYTVORENA: Final = _("common.message.ZADOST_O_SPOLUPRACI_VYTVORENA.text")  # Žádost o spolupráci byla vytvořena.
SPOLUPRACE_BYLA_AKTIVOVANA: Final = _("common.message.SPOLUPRACE_BYLA_AKTIVOVANA.text")  # Spolupráce byla aktivována.
SPOLUPRACE_BYLA_DEAKTIVOVANA: Final = _("common.message.SPOLUPRACE_BYLA_DEAKTIVOVANA.text")  # Spolupráce byla deaktivována.
SPOLUPRACI_NELZE_AKTIVOVAT: Final = _("common.message.SPOLUPRACI_NELZE_AKTIVOVAT.text")  # Spolupráci nejde aktivovat.
SPOLUPRACI_NELZE_DEAKTIVOVAT: Final = _("common.message.SPOLUPRACI_NELZE_DEAKTIVOVAT.text")  # Spolupráci nejde deaktivovat.

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
UPLOADFILE_REJECTED_DOKUMENT_MODEL: Final = _("core.message_constants.uploadFile.rejectedDokumentModel.text")
UPLOADFILE_REJECTED_ALL: Final = _("core.message_constants.uploadFile.rejectedAll.text")
UPLOADFILE_ERROR: Final = _("core.message_constants.uploadFile.error.text")

# Validation
VALIDATION_NOT_VALID: Final = _("common.message.VALIDATION_NOT_VALID.text")  # Geometrie není validní.
VALIDATION_EMPTY: Final = _("common.message.VALIDATION_EMPTY.text")  # Geometrie je prázdná.
VALIDATION_NOT_SIMPLE: Final = _("common.message.VALIDATION_NOT_SIMPLE.text")  # Geometrie není typu simple geometry.
VALIDATION_NOT_MULTIPART: Final = _("common.message.VALIDATION_NOT_MULTIPART.text")  # Geometrie je multigeometrií.
VALIDATION_LINE_LENGTH: Final = _("common.message.VALIDATION_LINE_LENGTH.text")  # Vzdálenost bodů je nižší než povolená mez.

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

#testovaci prostredi
NEPRODUKCNI_PROSTREDI_INFO: Final = _("core.message_constants.neprodukcniTestovaciProstredi.text")

#rosseta
TRANSLATION_UPLOAD_SUCCESS: Final = _("core.message_constants.translationUploadSucces.text")
TRANSLATION_DELETE_CANNOT_MAIN: Final = _("core.message_constants.translationDeleteCannotMain.text")
TRANSLATION_DELETE_SUCCESS: Final = _("core.message_constants.translationDeleteSucces.text")
TRANSLATION_DELETE_ERROR: Final = _("core.message_constants.translationDeleteError.text")
TRANSLATION_FILE_TOOSMALL: Final = _("core.message_constants.translationFileTooSmall.text")
TRANSLATION_FILE_WRONG_FORMAT: Final = _("core.message_constants.translationFileWrongFormat.text")

#restart aplikace
APPLICATION_RESTART_ERROR: Final = _("core.message_constants.applicationRestartError.text")
APPLICATION_RESTART_SUCCESS: Final = _("core.message_constants.applicationRestartSuccess.text")
