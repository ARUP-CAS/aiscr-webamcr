from webclient.settings.base import get_secret
from django.test.runner import DiscoverRunner as BaseRunner
import logging


logger = logging.getLogger(__name__)

USERS={ "archeolog":{"USERNAME":"archeolog1@arup.cas.cz" , "PASSWORD":"afsd15Easd#" },
       "archivar":  {"USERNAME":"archivar1@arup.cas.cz" , "PASSWORD":"afsd15Easd7" } , 
       "badatel":  {"USERNAME":"badatel2@arup.cas.cz" , "PASSWORD":"afsd15Easd2" } , 
        "badatel1":  {"USERNAME":"zdenek.omelka@email.cz" , "PASSWORD":"afsd15Easd3" } , 
}




class AMCRSeleniumTestRunner(BaseRunner):
    def setup_databases(self, *args, **kwargs):
        self.keepdb=True
        temp_return = super().setup_databases(*args, **kwargs)
        return temp_return  
        

    def teardown_databases(self, *args, **kwargs):
        # do somthing
        #return super().teardown_databases(*args, **kwargs)
        pass
        
