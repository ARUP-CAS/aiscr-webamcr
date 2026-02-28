from html.parser import HTMLParser
from io import StringIO


class MLStripper(HTMLParser):
    """Pomocná třída pro odstranění HTML značek z textu."""

    def __init__(self):
        """Inicializuje parser a interní textový buffer."""
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        """
        Ukládá textová data nalezená parserem.

        :param d: Popis parametru ``d``.
        """
        self.text.write(d)

    def get_data(self):
        """Vrátí text bez HTML značek načtený během parsování."""
        return self.text.getvalue()
