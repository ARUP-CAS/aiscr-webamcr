class PianNotInKladysm5Error(Exception):
    """Implementuje komponentu ``PianNotInKladysm5Error`` v rámci aplikace."""

    def __init__(
        self,
        pian,
        message="Pians geometry is not contained in any of the Kladysm map lists",
    ):
        """
        Inicializuje výjimku s odkazem na PIAN, jehož geometrie neleží v žádném kladu mapových listů.

        :param pian: Instance PIANu, jehož geometrie se nenachází v žádném kladu mapových listů.
        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.pian = pian
        self.message = message
        super().__init__(self.pian)


class MaximalIdentNumberError(Exception):
    """Implementuje komponentu ``MaximalIdentNumberError`` v rámci aplikace."""

    def __init__(self, number, message="Maximalni cislo identifikatoru bylo prekroceno"):
        """
        Inicializuje výjimku s číslem identifikátoru, které překročilo povolené maximum.

        :param number: Číslo identifikátoru, které překročilo maximální povolenou hodnotu.
        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.number = number
        self.message = message
        super().__init__(self.number)


class DJNemaPianError(Exception):
    """Implementuje komponentu ``DJNemaPianError`` v rámci aplikace."""

    def __init__(self, dj, message="Adb nelze vytvorit protoze DJ nema pian"):
        """
        Inicializuje výjimku pro případ, kdy dokumentační jednotka nemá přiřazen žádný PIAN.

        :param dj: Instance dokumentační jednotky, která postrádá přiřazený PIAN.
        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.dj = dj
        self.message = message
        super().__init__(self.dj)


class NelzeZjistitRaduError(Exception):
    """Implementuje komponentu ``NelzeZjistitRaduError`` v rámci aplikace."""

    def __init__(self, message="Nelze zjistit radu dokumentu"):
        """
        Inicializuje výjimku pro případ, kdy nelze určit řadu dokumentu.

        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.message = message


class NeocekavanaRadaError(Exception):
    """Implementuje komponentu ``NeocekavanaRadaError`` v rámci aplikace."""

    def __init__(self, message="Neocekavana rada dokumentu."):
        """
        Inicializuje výjimku pro případ, kdy je zjištěna neočekávaná řada dokumentu.

        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.message = message


class WrongSheetError(Exception):
    """Implementuje komponentu ``WrongSheetError`` v rámci aplikace."""

    def __init__(self, message="Excel nema spravne sloupce"):
        """
        Inicializuje výjimku pro případ, kdy importovaný Excel soubor nemá správné sloupce.

        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.message = message


class NeznamaGeometrieError(Exception):
    """Implementuje komponentu ``NeznamaGeometrieError`` v rámci aplikace."""

    def __init__(self, message="Neocekavana geometrie pianu."):
        """
        Inicializuje výjimku pro případ, kdy je zjištěn neznámý nebo neočekávaný typ geometrie PIANu.

        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.message = message


class UnexpectedDataRelations(Exception):
    """Implementuje komponentu ``UnexpectedDataRelations`` v rámci aplikace."""

    def __init__(self, message="Duplicitni nebo chybejici relace."):
        """
        Inicializuje výjimku pro případ duplicitních nebo chybějících datových relací při importu.

        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.message = message


class MaximalEventCount(Exception):
    """Implementuje komponentu ``MaximalEventCount`` v rámci aplikace."""

    def __init__(self, number, message="Maximalni pocet akci prekrocen"):
        """
        Inicializuje výjimku pro případ, kdy byl překročen maximální počet archeologických akcí.

        :param number: Aktuální počet akcí, jenž překročil povolené maximum.
        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.number = number
        self.message = message
        super().__init__(self.number)


class WrongCSVError(Exception):
    """Implementuje komponentu ``WrongCSVError`` v rámci aplikace."""

    def __init__(self, message="CSV nema spravne sloupce"):
        """
        Inicializuje výjimku pro případ, kdy importovaný CSV soubor nemá správné sloupce.

        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.message = message


class ZaznamSouborNotmatching(Exception):
    """Implementuje komponentu ``ZaznamSouborNotmatching`` v rámci aplikace."""

    def __init__(self, message="Zaznam nema dany soubor"):
        """
        Inicializuje výjimku pro případ, kdy záznam AMČR neobsahuje očekávaný soubor.

        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.message = message


class StateChangedError(Exception):
    """Implementuje komponentu ``StateChangedError`` v rámci aplikace."""

    def __init__(self, message="Záznam byl mezitím změměn"):
        """
        Inicializuje výjimku pro případ, kdy byl stav záznamu AMČR změněn jiným uživatelem od jeho načtení.

        :param message: Textová zpráva popisující důvod výjimky.
        """
        self.message = message
