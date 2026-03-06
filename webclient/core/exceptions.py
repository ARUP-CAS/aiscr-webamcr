class PianNotInKladysm5Error(Exception):
    """Implementuje komponentu ``PianNotInKladysm5Error`` v rámci aplikace."""

    def __init__(
        self,
        pian,
        message="Pians geometry is not contained in any of the Kladysm map lists",
    ):
        """
        Inicializuje instanci třídy.

        :param pian: Parametr ``pian`` slouží jako vstup pro logiku funkce ``__init__``.
        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.pian = pian
        self.message = message
        super().__init__(self.pian)


class MaximalIdentNumberError(Exception):
    """Implementuje komponentu ``MaximalIdentNumberError`` v rámci aplikace."""

    def __init__(self, number, message="Maximalni cislo identifikatoru bylo prekroceno"):
        """
        Inicializuje instanci třídy.

        :param number: Parametr ``number`` slouží jako vstup pro logiku funkce ``__init__``.
        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.number = number
        self.message = message
        super().__init__(self.number)


class DJNemaPianError(Exception):
    """Implementuje komponentu ``DJNemaPianError`` v rámci aplikace."""

    def __init__(self, dj, message="Adb nelze vytvorit protoze DJ nema pian"):
        """
        Inicializuje instanci třídy.

        :param dj: Parametr ``dj`` slouží jako vstup pro logiku funkce ``__init__``.
        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.dj = dj
        self.message = message
        super().__init__(self.dj)


class NelzeZjistitRaduError(Exception):
    """Implementuje komponentu ``NelzeZjistitRaduError`` v rámci aplikace."""

    def __init__(self, message="Nelze zjistit radu dokumentu"):
        """
        Inicializuje instanci třídy.

        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.message = message


class NeocekavanaRadaError(Exception):
    """Implementuje komponentu ``NeocekavanaRadaError`` v rámci aplikace."""

    def __init__(self, message="Neocekavana rada dokumentu."):
        """
        Inicializuje instanci třídy.

        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.message = message


class WrongSheetError(Exception):
    """Implementuje komponentu ``WrongSheetError`` v rámci aplikace."""

    def __init__(self, message="Excel nema spravne sloupce"):
        """
        Inicializuje instanci třídy.

        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.message = message


class NeznamaGeometrieError(Exception):
    """Implementuje komponentu ``NeznamaGeometrieError`` v rámci aplikace."""

    def __init__(self, message="Neocekavana geometrie pianu."):
        """
        Inicializuje instanci třídy.

        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.message = message


class UnexpectedDataRelations(Exception):
    """Implementuje komponentu ``UnexpectedDataRelations`` v rámci aplikace."""

    def __init__(self, message="Duplicitni nebo chybejici relace."):
        """
        Inicializuje instanci třídy.

        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.message = message


class MaximalEventCount(Exception):
    """Implementuje komponentu ``MaximalEventCount`` v rámci aplikace."""

    def __init__(self, number, message="Maximalni pocet akci prekrocen"):
        """
        Inicializuje instanci třídy.

        :param number: Parametr ``number`` slouží jako vstup pro logiku funkce ``__init__``.
        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.number = number
        self.message = message
        super().__init__(self.number)


class WrongCSVError(Exception):
    """Implementuje komponentu ``WrongCSVError`` v rámci aplikace."""

    def __init__(self, message="CSV nema spravne sloupce"):
        """
        Inicializuje instanci třídy.

        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.message = message


class ZaznamSouborNotmatching(Exception):
    """Implementuje komponentu ``ZaznamSouborNotmatching`` v rámci aplikace."""

    def __init__(self, message="Zaznam nema dany soubor"):
        """
        Inicializuje instanci třídy.

        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.message = message


class StateChangedError(Exception):
    """Implementuje komponentu ``StateChangedError`` v rámci aplikace."""

    def __init__(self, message="Záznam byl mezitím změměn"):
        """
        Inicializuje instanci třídy.

        :param message: Parametr ``message`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        self.message = message
