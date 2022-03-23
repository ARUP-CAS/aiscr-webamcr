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
PROJEKT_NEKDO_ZMENIL_STAV: Final = _("projekt.message.zmenaStavuNekymJinym.text")

AKCE_USPESNE_ZAPSANA: Final = "Akce úspěšně zapsána."
AKCE_USPESNE_ODESLANA: Final = "Akce úspěšně odeslána."
AKCE_USPESNE_ARCHIVOVANA: Final = "Akce úspěšně archivovaná."
AKCE_USPESNE_VRACENA: Final = "Akce úspěšně vrácena."
AKCI_NELZE_ODESLAT: Final = "Akci nelze odeslat."
AKCI_NELZE_ARCHIVOVAT: Final = "Akci nelze archivovat."
AKCI_NEKDO_ZMENIL_STAV: Final = _("akce.message.zmenaStavuNekymJinym.text")

DOKUMENT_USPESNE_ODESLAN: Final = "Dokument úspěšně odeslán."
DOKUMENT_USPESNE_ARCHIVOVAN: Final = "Dokument úspěšně archivován."
DOKUMENT_USPESNE_VRACEN: Final = "Dokument úspěšně vrácen."
DOKUMENT_NELZE_ODESLAT: Final = "Dokument nelze odeslat."
DOKUMENT_NELZE_ARCHIVOVAT: Final = "Dokument nelze archivovat."
DOKUMENT_USPESNE_PRIPOJEN: Final = "Dokument úspěšně připojen."
DOKUMENT_JIZ_BYL_PRIPOJEN: Final = "Dokument již byl připojen!"
DOKUMENT_USPESNE_ODPOJEN: Final = "Dokument úspěšně odpojen."
VYBERTE_PROSIM_POLOHU: Final = "Vyberte prosím lokalizaci na mapě."
DOKUMENT_NEKDO_ZMENIL_STAV: Final = _("dokument.message.zmenaStavuNekymJinym.text")

# Osoba
OSOBA_USPESNE_PRIDANA: Final = "Osoba úspěšně přidána."
OSOBA_JIZ_EXISTUJE: Final = "Jméno již existuje."

# Pian
PIAN_USPESNE_ODPOJEN: Final = "Pian uspesne odpojen."
PIAN_USPESNE_POTVRZEN: Final = "Pian uspesne potvrzen."
PIAN_USPESNE_SMAZAN: Final = "Pian byl smazán."

# SN
SAMOSTATNY_NALEZ_VRACEN: Final = "Samostatný nález vrácen do předchozího stavu."
SAMOSTATNY_NALEZ_NELZE_ODESLAT: Final = "Samostatný nález nelze odeslat."
SAMOSTATNY_NALEZ_ODESLAN: Final = "Samostatný nález úspěšně odeslán."
SAMOSTATNY_NALEZ_POTVRZEN: Final = "Samostatný nález úspěšně potvrzen."
SAMOSTATNY_NALEZ_ARCHIVOVAN: Final = "Samostatný nález úspěšně archivován."
SAMOSTATNY_NALEZ_NEKDO_ZMENIL_STAV: Final = _("pas.message.zmenaStavuNekymJinym.text")

# Spoluprace
ZADOST_O_SPOLUPRACI_VYTVORENA: Final = "Žádost o spolupráci byla vytvořena."
SPOLUPRACE_BYLA_AKTIVOVANA: Final = "Spolupráce byla aktivována."
SPOLUPRACE_BYLA_DEAKTIVOVANA: Final = "Spolupráce byla deaktivována."
SPOLUPRACI_NELZE_AKTIVOVAT: Final = "Spolupráci nejde aktivovat."
SPOLUPRACI_NELZE_DEAKTIVOVAT: Final = "Spolupráci nejde deaktivovat."


# Auto-logout
AUTOLOGOUT_AFTER_LOGOUT: Final = _("autologout.message.afterlogout.text")
AUTOLOGOUT_EXPIRATION_WARNING: Final = _("autologout.message.expirationwarning.text")
AUTOLOGOUT_REFRESH_ERROR: Final = _("autologout.message.refresherror.text")
AUTOLOGOUT_REFRESH_SUCCESS: Final = _("autologout.message.refreshsuccess.text")

# DropZone upload messages
UPLOADFILE_REJECTED_PAS: Final = _("core.message.uploadFile.rejectedPas.text")
UPLOADFILE_REJECTED_DOKUMENT: Final = _("core.message.uploadFile.rejectedDokument.text")
UPLOADFILE_REJECTED_ALL: Final = _("core.message.uploadFile.rejectedAll.text")
