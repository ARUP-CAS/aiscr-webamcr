from django_tables2 import tables
from historie.models import Historie


class HistorieTable(tables.Table):
    class Meta:
        model = Historie
        template_name = "django_tables2/bootstrap4.html"
        fields = (
            "typ_zmeny",
            "datum_zmeny",
            "uzivatel",
            "poznamka",
        )

    # TODO: This form of printing does not respect django timezone
    # @staticmethod
    # def render_datum_zmeny(value):
    #     if value:
    #         return value.strftime("%Y/%m/%d, %H:%M:%S")
    #     else:
    #         return "—"
