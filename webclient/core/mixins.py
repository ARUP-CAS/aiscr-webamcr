import structlog
from django.core.exceptions import ObjectDoesNotExist

logger_s = structlog.get_logger(__name__)


class ManyToManyRestrictedClassMixin:
    @property
    def has_connections(self):
        attr_list = []
        for attr in dir(self):
            if not attr.startswith("_") and attr not in ("has_connections", "objects"):
                try:
                    if hasattr(getattr(self, attr), "all"):
                        attr_list.append(attr)
                except ObjectDoesNotExist as err:
                    logger_s.debug("core.mixins.ManyToManyRestrictedClassMixin.has_connections.ObjectDoesNotExist",
                                   err=err)
        attr_list = [attr for attr in attr_list if getattr(self, attr).all().count() > 0]
        return len(attr_list) > 0
