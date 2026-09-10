import itertools
import logging
import unittest.runner

from django.test.runner import DiscoverRunner as BaseRunner
from django.test.utils import override_settings

logger = logging.getLogger(__name__)

#: Platnost session cookie po dobu běhu testů (v sekundách).
#:
#: Projekt používá ``SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"``,
#: takže session je uložená přímo v podepsané cookie a její stáří se počítá
#: z podpisového razítka proti ``SESSION_COOKIE_AGE``. Selenium testy ale běží
#: pod ``freeze_time`` s pevným datem, které je vůči reálnému času klidně
#: měsíce v minulosti.
TEST_SESSION_COOKIE_AGE = 60 * 60 * 24 * 365 * 20  # 20 let

USERS = {
    "archeolog": {"USERNAME": "archeolog1@arup.cas.cz", "PASSWORD": "afsd15Easd#"},
    "archivar": {"USERNAME": "archivar1@arup.cas.cz", "PASSWORD": "afsd15Easd7"},
    "badatel": {"USERNAME": "badatel2@arup.cas.cz", "PASSWORD": "afsd15Easd2"},
    "badatel1": {"USERNAME": "badatel1@email.cz", "PASSWORD": "afsd15Easd3"},
    "administrator": {"USERNAME": "administrator1@arup.cas.cz", "PASSWORD": "afsd15Easd1"},
    "ADMIN_USER": {"USERNAME": "amcr@arup.cas.cz", "PASSWORD": ""},
}
TYP_DJ_CELEK_AKCE_ID = ""


class CustomTextTestResult(unittest.runner.TextTestResult):
    """Rozšíření třídy TextTestResult s podporou číslování testovacích případů."""

    def __init__(self, stream, descriptions, verbosity):
        """
        Inicializuje generátor čísel testů a poté zavolá implementaci předka.

        :param stream: Parametr ``stream`` předává se do volání ``__init__()``, vstupuje do návratové hodnoty.
        :param descriptions: Parametr ``descriptions`` předává se do volání ``__init__()``, vstupuje do návratové hodnoty.
        :param verbosity: Parametr ``verbosity`` předává se do volání ``__init__()``, vstupuje do návratové hodnoty.
        :return: Vrací výsledek volání ``__init__()``.
        """

        self.test_numbers = itertools.count(1)

        return super(CustomTextTestResult, self).__init__(stream, descriptions, verbosity)

    def startTest(self, test):
        """
        Pokud je showAll zapnuto, zapíše číslo testu do výstupu a poté zavolá implementaci předka.

        :param test: Test case nebo testovací objekt, se kterým runner pracuje.

            :return: Vrací výsledek volání ``startTest()``.
        """

        if True:  # self.showAll:
            progress = "[{0}/{1}] ".format(next(self.test_numbers), self.test_case_count)
            self.stream.write(progress)

            # Průběh ukládá i do samotného testu, aby se při chybě
            # mohl propsat do informací o výjimce v našem přepsaném runneru.
            # metoda _exec_info_to_string:
            test.progress_index = progress

        return super(CustomTextTestResult, self).startTest(test)

    def _exc_info_to_string(self, err, test):
        """
        Získá text informací o výjimce z předka a na začátek přidá řádek s číslem testu.

        :param err: Parametr ``err`` předává se do volání ``_exc_info_to_string()``.
        :param test: Parametr ``test`` předává se do volání ``_exc_info_to_string()``, ``format()``, pracuje se s atributy ``progress_index``.
        :return: Vrací proměnná ``info``.
        """

        info = super(CustomTextTestResult, self)._exc_info_to_string(err, test)

        if self.showAll:
            info = "Test number: {index}\n{info}".format(index=test.progress_index, info=info)

        return info


class CustomTextTestRunner(unittest.runner.TextTestRunner):
    """Rozšíření třídy TextTestRunner s podporou číslování testovacích případů."""

    resultclass = CustomTextTestResult

    def run(self, test):
        """
        Spustí hodnotu. v aplikaci.

        :param test: Test case nebo testovací objekt, se kterým runner pracuje.

            :return: Vrací výsledek volání ``run()``.
        """

        self.test_case_count = test.countTestCases()
        return super(CustomTextTestRunner, self).run(test)

    def _makeResult(self):
        """
               Provádí operaci makeResult.

        :return: Výstup funkce odpovídající implementované logice.
        """

        result = super(CustomTextTestRunner, self)._makeResult()
        result.test_case_count = self.test_case_count
        return result


class AMCRSeleniumTestRunner(BaseRunner):
    """Implementuje komponentu ``AMCRSeleniumTestRunner`` v rámci aplikace."""

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(AMCRSeleniumTestRunner, self).__init__(*args, **kwargs)
        self.test_runner = CustomTextTestRunner
        self._session_cookie_age_override = None

    def setup_test_environment(self, **kwargs):
        """
        Připraví testovací prostředí a prodlouží platnost session cookie.

        Viz :data:`TEST_SESSION_COOKIE_AGE` – bez prodloužení ztrácejí testy
        běžící pod ``freeze_time`` session, jakmile se hodiny vrátí do
        reálného času.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``setup_test_environment()``.
        """
        super().setup_test_environment(**kwargs)
        self._session_cookie_age_override = override_settings(SESSION_COOKIE_AGE=TEST_SESSION_COOKIE_AGE)
        self._session_cookie_age_override.enable()

    def teardown_test_environment(self, **kwargs):
        """
        Vrátí původní ``SESSION_COOKIE_AGE`` a uklidí testovací prostředí.

        :param kwargs: Parametr ``kwargs`` se předává do volání ``teardown_test_environment()``.
        """
        if self._session_cookie_age_override is not None:
            self._session_cookie_age_override.disable()
            self._session_cookie_age_override = None
        super().teardown_test_environment(**kwargs)

    def setup_databases(self, *args, **kwargs):
        """
        Připraví instanci testovací databáze

        :param args: Parametr ``args`` se předává do volání ``setup_databases()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``setup_databases()``.

        :return: Vrací proměnná ``temp_return``.
        """
        self.keepdb = True
        temp_return = super().setup_databases(*args, **kwargs)
        return temp_return

    def teardown_databases(self, *args, **kwargs):
        # do somthing
        # return super().teardown_databases(*args, **kwargs)
        """
        Smaže testovací databáze a vyčistí jejich prostředky.

        :param args: Parametr ``args`` se předává do volání ``teardown_databases()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``teardown_databases()``.
        """
        pass
