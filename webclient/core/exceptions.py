class PianNotInKladysm5Error(Exception):
    """Zapouzdřuje chování třídy ``PianNotInKladysm5Error`` pro modul ``webclient.core.exceptions``."""
    def __init__(
        self,
        pian,
        message="Pians geometry is not contained in any of the Kladysm map lists",
    ):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param pian: Vstupní hodnota parametru ``pian`` použitého při zpracování.
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.pian = pian
        self.message = message
        super().__init__(self.pian)


class MaximalIdentNumberError(Exception):
    """Zapouzdřuje chování třídy ``MaximalIdentNumberError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, number, message="Maximalni cislo identifikatoru bylo prekroceno"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param number: Vstupní hodnota parametru ``number`` použitého při zpracování.
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.number = number
        self.message = message
        super().__init__(self.number)


class DJNemaPianError(Exception):
    """Zapouzdřuje chování třídy ``DJNemaPianError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, dj, message="Adb nelze vytvorit protoze DJ nema pian"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param dj: Vstupní hodnota parametru ``dj`` použitého při zpracování.
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.dj = dj
        self.message = message
        super().__init__(self.dj)


class NelzeZjistitRaduError(Exception):
    """Zapouzdřuje chování třídy ``NelzeZjistitRaduError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Nelze zjistit radu dokumentu"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.message = message


class NeocekavanaRadaError(Exception):
    """Zapouzdřuje chování třídy ``NeocekavanaRadaError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Neocekavana rada dokumentu."):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.message = message


class WrongSheetError(Exception):
    """Zapouzdřuje chování třídy ``WrongSheetError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Excel nema spravne sloupce"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.message = message


class NeznamaGeometrieError(Exception):
    """Zapouzdřuje chování třídy ``NeznamaGeometrieError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Neocekavana geometrie pianu."):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.message = message


class UnexpectedDataRelations(Exception):
    """Zapouzdřuje chování třídy ``UnexpectedDataRelations`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Duplicitni nebo chybejici relace."):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.message = message


class MaximalEventCount(Exception):
    """Zapouzdřuje chování třídy ``MaximalEventCount`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, number, message="Maximalni pocet akci prekrocen"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param number: Vstupní hodnota parametru ``number`` použitého při zpracování.
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.number = number
        self.message = message
        super().__init__(self.number)


class WrongCSVError(Exception):
    """Zapouzdřuje chování třídy ``WrongCSVError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="CSV nema spravne sloupce"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.message = message


class ZaznamSouborNotmatching(Exception):
    """Zapouzdřuje chování třídy ``ZaznamSouborNotmatching`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Zaznam nema dany soubor"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.message = message


class StateChangedError(Exception):
    """Zapouzdřuje chování třídy ``StateChangedError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Záznam byl mezitím změměn"):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param message: Vstupní hodnota parametru ``message`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        self.message = message
