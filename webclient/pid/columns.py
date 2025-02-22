import django_tables2 as tables
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


class DoiColumn(tables.columns.ManyToManyColumn):
    def __init__(self, *args, **kwargs):
        self.render_property_name = kwargs.pop("render_property_name", None)
        super(DoiColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        items = [
            getattr(item, self.render_property_name)
            for item in self.filter(value)
            if getattr(item, self.render_property_name, None)
        ]
        return mark_safe(conditional_escape(self.separator).join(items))
