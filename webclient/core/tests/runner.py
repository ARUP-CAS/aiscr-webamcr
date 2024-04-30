from webclient.settings.base import get_secret
from django.test.runner import DiscoverRunner as BaseRunner
import logging
import unittest
import unittest.runner
import itertools
import collections

logger = logging.getLogger(__name__)

USERS={ "archeolog":{"USERNAME":"archeolog1@arup.cas.cz" , "PASSWORD":"afsd15Easd#" },
       "archivar":  {"USERNAME":"archivar1@arup.cas.cz" , "PASSWORD":"afsd15Easd7" } , 
       "badatel":  {"USERNAME":"badatel2@arup.cas.cz" , "PASSWORD":"afsd15Easd2" } , 
        "badatel1":  {"USERNAME":"zdenek.omelka@email.cz" , "PASSWORD":"afsd15Easd3" } , 
}

class CustomTextTestResult(unittest.runner.TextTestResult):
    """Extension of TextTestResult to support numbering test cases"""

    def __init__(self, stream, descriptions, verbosity):
        """Initializes the test number generator, then calls super impl"""

        self.test_numbers = itertools.count(1)

        return super(CustomTextTestResult, self).__init__(stream, descriptions, verbosity)

    def startTest(self, test):
        """Writes the test number to the stream if showAll is set, then calls super impl"""

        if True:# self.showAll:
            progress = '[{0}/{1}] '.format(next(self.test_numbers), self.test_case_count)
            self.stream.write(progress)

            # Also store the progress in the test itself, so that if it errors,
            # it can be written to the exception information by our overridden
            # _exec_info_to_string method:
            test.progress_index = progress

        return super(CustomTextTestResult, self).startTest(test)

    def _exc_info_to_string(self, err, test):
        """Gets an exception info string from super, and prepends 'Test Number' line"""

        info = super(CustomTextTestResult, self)._exc_info_to_string(err, test)

        if self.showAll:
            info = 'Test number: {index}\n{info}'.format(
                index=test.progress_index,
                info=info
            )

        return info
    
class CustomTextTestRunner(unittest.runner.TextTestRunner):
    """Extension of TextTestRunner to support numbering test cases"""

    resultclass = CustomTextTestResult

    def run(self, test):
        """Stores the total count of test cases, then calls super impl"""

        self.test_case_count = test.countTestCases()
        return super(CustomTextTestRunner, self).run(test)

    def _makeResult(self):
        """Creates and returns a result instance that knows the count of test cases"""

        result = super(CustomTextTestRunner, self)._makeResult()
        result.test_case_count = self.test_case_count
        return result


class AMCRSeleniumTestRunner(BaseRunner):
    def __init__(self, *args, **kwargs):        
        super(AMCRSeleniumTestRunner, self).__init__(*args, **kwargs)
        self.test_runner=CustomTextTestRunner
    
    
    def setup_databases(self, *args, **kwargs):
        self.keepdb=True
        temp_return = super().setup_databases(*args, **kwargs)
        return temp_return  
        

    def teardown_databases(self, *args, **kwargs):
        # do somthing
        #return super().teardown_databases(*args, **kwargs)
        pass
        
