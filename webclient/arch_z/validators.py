import datetime
from django import forms


def datum_max_1_mesic_v_budoucnosti(value):
    if value > datetime.date.today() + datetime.timedelta(days=30):
        raise forms.ValidationError("Datum nesmí být dále než měsíc v budoucnosti")
    return value
