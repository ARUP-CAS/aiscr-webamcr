class PianNotInKladysm5Error(Exception):
    def __init__(
        self,
        pian,
        message="Pians geometry is not contained in any of the Kladysm map lists",
    ):
        self.pian = pian
        self.message = message
        super().__init__(self.pian)


class MaximalIdentNumberError(Exception):
    def __init__(self, number, message="Maximalni cislo identifikatoru bylo prekroceno"):
        self.number = number
        self.message = message
        super().__init__(self.number)


class DJNemaPianError(Exception):
    def __init__(self, dj, message="Adb nelze vytvorit protoze DJ nema pian"):
        self.dj = dj
        self.message = message
        super().__init__(self.dj)


class NelzeZjistitRaduError(Exception):
    def __init__(self, message="Nelze zjistit radu dokumentu"):
        self.message = message


class NeocekavanaRadaError(Exception):
    def __init__(self, message="Neocekavana rada dokumentu."):
        self.message = message


class WrongSheetError(Exception):
    def __init__(self, message="Excel nema spravne sloupce"):
        self.message = message


class NeznamaGeometrieError(Exception):
    def __init__(self, message="Neocekavana geometrie pianu."):
        self.message = message


class UnexpectedDataRelations(Exception):
    def __init__(self, message="Duplicitni nebo chybejici relace."):
        self.message = message


class MaximalEventCount(Exception):
    def __init__(self, number, message="Maximalni pocet akci prekrocen"):
        self.number = number
        self.message = message
        super().__init__(self.number)


class WrongCSVError(Exception):
    def __init__(self, message="CSV nema spravne sloupce"):
        self.message = message


class ZaznamSouborNotmatching(Exception):
    def __init__(self, message="Zaznam nema dany soubor"):
        self.message = message
