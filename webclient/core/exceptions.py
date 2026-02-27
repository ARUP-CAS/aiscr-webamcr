class PianNotInKladysm5Error(Exception):
    """Třída `PianNotInKladysm5Error` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(
        self,
        pian,
        message="Pians geometry is not contained in any of the Kladysm map lists",
    ):
        """Funkce `PianNotInKladysm5Error.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param pian: Vstupní hodnota používaná při zpracování.
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.pian = pian
        self.message = message
        super().__init__(self.pian)


class MaximalIdentNumberError(Exception):
    """Třída `MaximalIdentNumberError` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, number, message="Maximalni cislo identifikatoru bylo prekroceno"):
        """Funkce `MaximalIdentNumberError.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param number: Vstupní hodnota používaná při zpracování.
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.number = number
        self.message = message
        super().__init__(self.number)


class DJNemaPianError(Exception):
    """Třída `DJNemaPianError` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, dj, message="Adb nelze vytvorit protoze DJ nema pian"):
        """Funkce `DJNemaPianError.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param dj: Vstupní hodnota používaná při zpracování.
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.dj = dj
        self.message = message
        super().__init__(self.dj)


class NelzeZjistitRaduError(Exception):
    """Třída `NelzeZjistitRaduError` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, message="Nelze zjistit radu dokumentu"):
        """Funkce `NelzeZjistitRaduError.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.message = message


class NeocekavanaRadaError(Exception):
    """Třída `NeocekavanaRadaError` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, message="Neocekavana rada dokumentu."):
        """Funkce `NeocekavanaRadaError.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.message = message


class WrongSheetError(Exception):
    """Třída `WrongSheetError` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, message="Excel nema spravne sloupce"):
        """Funkce `WrongSheetError.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.message = message


class NeznamaGeometrieError(Exception):
    """Třída `NeznamaGeometrieError` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, message="Neocekavana geometrie pianu."):
        """Funkce `NeznamaGeometrieError.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.message = message


class UnexpectedDataRelations(Exception):
    """Třída `UnexpectedDataRelations` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, message="Duplicitni nebo chybejici relace."):
        """Funkce `UnexpectedDataRelations.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.message = message


class MaximalEventCount(Exception):
    """Třída `MaximalEventCount` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, number, message="Maximalni pocet akci prekrocen"):
        """Funkce `MaximalEventCount.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param number: Vstupní hodnota používaná při zpracování.
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.number = number
        self.message = message
        super().__init__(self.number)


class WrongCSVError(Exception):
    """Třída `WrongCSVError` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, message="CSV nema spravne sloupce"):
        """Funkce `WrongCSVError.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.message = message


class ZaznamSouborNotmatching(Exception):
    """Třída `ZaznamSouborNotmatching` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, message="Zaznam nema dany soubor"):
        """Funkce `ZaznamSouborNotmatching.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.message = message


class StateChangedError(Exception):
    """Třída `StateChangedError` v modulu `webclient.core.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, message="Záznam byl mezitím změměn"):
        """Funkce `StateChangedError.__init__` v modulu `webclient.core.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param message: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        self.message = message
