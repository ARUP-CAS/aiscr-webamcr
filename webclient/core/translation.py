from django.utils.translation import gettext


def format_message(message_id, **params) -> str:
    """
    Přeloží zprávu s pojmenovanými zástupnými znaky a dosadí do ní parametry.

    Překlad drží celou větu (``{child}``, ``{field}`` …), takže pořadí slov řídí překladatel,
    ne skládání fragmentů v kódu. Chybí-li překlad (``gettext`` vrátí ID doslova), parametry se
    připojí za ID ve tvaru ``klíč=hodnota``, aby se informace ze zprávy neztratila. Překlad
    s neznámým zástupným znakem se vrátí bez dosazení místo vyvolání výjimky.

    Volající označí ID pomocí ``gettext_noop``, aby ho ``makemessages`` extrahoval.

    :param message_id: Překladové ID zprávy.
    :param params: Hodnoty pro zástupné znaky v přeložené zprávě.
    :return: Přeložená zpráva s dosazenými hodnotami.
    """
    text = str(gettext(message_id))
    if text == message_id:
        return " ".join([message_id] + [f"{key}={value}" for key, value in params.items()])
    try:
        return text.format(**params)
    except (KeyError, IndexError, ValueError):
        return text
