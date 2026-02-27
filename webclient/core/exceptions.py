class PianNotInKladysm5Error(Exception):
    """Zapouzdřuje chování třídy ``PianNotInKladysm5Error`` pro modul ``webclient.core.exceptions``."""
    def __init__(
        self,
        pian,
        message="Pians geometry is not contained in any of the Kladysm map lists",
    ):
        """Provádí funkci ``PianNotInKladysm5Error.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.pian = pian
        self.message = message
        super().__init__(self.pian)


class MaximalIdentNumberError(Exception):
    """Zapouzdřuje chování třídy ``MaximalIdentNumberError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, number, message="Maximalni cislo identifikatoru bylo prekroceno"):
        """Provádí funkci ``MaximalIdentNumberError.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.number = number
        self.message = message
        super().__init__(self.number)


class DJNemaPianError(Exception):
    """Zapouzdřuje chování třídy ``DJNemaPianError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, dj, message="Adb nelze vytvorit protoze DJ nema pian"):
        """Provádí funkci ``DJNemaPianError.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.dj = dj
        self.message = message
        super().__init__(self.dj)


class NelzeZjistitRaduError(Exception):
    """Zapouzdřuje chování třídy ``NelzeZjistitRaduError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Nelze zjistit radu dokumentu"):
        """Zpracuje volání ``NelzeZjistitRaduError.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.message = message


class NeocekavanaRadaError(Exception):
    """Zapouzdřuje chování třídy ``NeocekavanaRadaError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Neocekavana rada dokumentu."):
        """Zpracuje volání ``NeocekavanaRadaError.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.message = message


class WrongSheetError(Exception):
    """Zapouzdřuje chování třídy ``WrongSheetError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Excel nema spravne sloupce"):
        """Zpracuje volání ``WrongSheetError.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.message = message


class NeznamaGeometrieError(Exception):
    """Zapouzdřuje chování třídy ``NeznamaGeometrieError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Neocekavana geometrie pianu."):
        """Zpracuje volání ``NeznamaGeometrieError.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.message = message


class UnexpectedDataRelations(Exception):
    """Zapouzdřuje chování třídy ``UnexpectedDataRelations`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Duplicitni nebo chybejici relace."):
        """Zpracuje volání ``UnexpectedDataRelations.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.message = message


class MaximalEventCount(Exception):
    """Zapouzdřuje chování třídy ``MaximalEventCount`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, number, message="Maximalni pocet akci prekrocen"):
        """Provádí funkci ``MaximalEventCount.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.number = number
        self.message = message
        super().__init__(self.number)


class WrongCSVError(Exception):
    """Zapouzdřuje chování třídy ``WrongCSVError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="CSV nema spravne sloupce"):
        """Zpracuje volání ``WrongCSVError.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.message = message


class ZaznamSouborNotmatching(Exception):
    """Zapouzdřuje chování třídy ``ZaznamSouborNotmatching`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Zaznam nema dany soubor"):
        """Zpracuje volání ``ZaznamSouborNotmatching.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.message = message


class StateChangedError(Exception):
    """Zapouzdřuje chování třídy ``StateChangedError`` pro modul ``webclient.core.exceptions``."""
    def __init__(self, message="Záznam byl mezitím změměn"):
        """Zpracuje volání ``StateChangedError.__init__`` v rámci modulu ``webclient.core.exceptions``."""
        self.message = message
