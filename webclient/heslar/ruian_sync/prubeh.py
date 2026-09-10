"""
Sdílený výpis průběhu dlouhých běhů synchronizace RÚIAN.

Vlastní modul proto, že ho potřebuje :mod:`heslar.ruian_sync.syncer`
i :mod:`heslar.ruian_sync.reassign` – a syncer už reassign importuje, takže
opačný import by kruh uzavřel.
"""


def print_progress(label: str, current: int, total: int, last_pct: int) -> int:
    """
    Vypíše průběh, ale jen když se posunul o celé procento.

    Bez téhle podmínky by běh přes desítky tisíc záznamů vygeneroval stejný
    počet řádků výstupu.

    :param label: Popisek kroku, který se vypisuje před počty.
    :param current: Kolik položek je hotovo.
    :param total: Kolik jich je celkem; nekladná hodnota výpis přeskočí.
    :param last_pct: Naposledy vypsaná procenta (výstup předchozího volání).
    :return: Procenta k předání do dalšího volání.
    """
    if total <= 0:
        return last_pct
    pct = int(current * 100 / total)
    if pct > last_pct:
        print(f"  {label}: {current}/{total} ({pct}%)", flush=True)
        return pct
    return last_pct
