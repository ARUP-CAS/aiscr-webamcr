from django import forms


class ForeignKeyReadOnlyTextInput(forms.TextInput):
    """
    Widget pro textinput pro vazbu cizí klíč.
    """

    def __init__(self, value=None, attrs=None):
        if attrs is None:
            attrs = {}
        attrs["readonly"] = True
        super().__init__(attrs)
        self.value = None

    def format_value(self, value):
        return str(self.value)
