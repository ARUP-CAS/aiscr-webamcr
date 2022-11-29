class ManyToManyRestrictedClassMixin:
    @property
    def has_connections(self):
        attr_list = [attr for attr in dir(self) if not attr.startswith("_")
                     and attr not in ("has_connections", "objects")
                     and hasattr(getattr(self, attr), "all")]
        attr_list = [attr for attr in attr_list if getattr(self, attr).all().count() > 0]
        return len(attr_list) > 0
