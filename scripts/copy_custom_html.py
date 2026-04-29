"""
Zkopíruje vlastní HTML šablony do datového svazku nginx a zachová stávající obsah nadpisů p.

U každého souboru HTML ve zdrojovém adresáři, pokud již cílový soubor existuje,
se text nadpisu p uloží a obnoví v nově zkopírované šabloně.
"""

import os
import shutil

from bs4 import BeautifulSoup

SRC = "/custom_html"
DST = "/vol/web/nginx/data"


def copy_with_preserved_p(src: str, dst: str) -> None:
    """
    Zkopíruje HTML šablony ze zdrojového adresáře do cílového, přičemž zachová obsah elementu p.

    Pro každý HTML soubor ve zdrojovém adresáři: pokud cílový soubor existuje,
    uloží se text jeho p a po zkopírování nové šablony se obnoví.

    :param src: Zdrojový adresář s novými HTML šablonami.
    :param dst: Cílový adresář (persistentní volume).
    """
    for root, dirs, files in os.walk(src):
        for filename in files:
            if not filename.endswith(".html"):
                continue
            src_file = os.path.join(root, filename)
            rel_path = os.path.relpath(src_file, src)
            dst_file = os.path.join(dst, rel_path)

            # Save existing p content if destination exists
            p_text = None
            if os.path.exists(dst_file):
                with open(dst_file, encoding="utf-8") as fp:
                    soup = BeautifulSoup(fp, "html.parser")
                    p = soup.find("p")
                    if p and p.string:
                        p_text = str(p.string)

            # Copy new template (overwrite)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)

            # Restore p content if it was saved
            if p_text is not None:
                with open(dst_file, encoding="utf-8") as fp:
                    soup = BeautifulSoup(fp, "html.parser")
                p = soup.find("p")
                if p:
                    p.string = p_text
                with open(dst_file, "w", encoding="utf-8") as fp:
                    fp.write(str(soup))


if __name__ == "__main__":
    copy_with_preserved_p(SRC, DST)
