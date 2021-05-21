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
    def __init__(
        self, number, message="Maximalni cislo identifikatoru bylo prekroceno"
    ):
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


class NeznamaGeometrieError(Exception):
    def __init__(self, message="Neocekavana geometrie pianu."):
        self.message = message
