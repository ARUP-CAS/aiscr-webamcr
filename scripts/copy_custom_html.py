"""
Copy custom HTML templates to the nginx data volume, preserving existing h1 content.

For each HTML file in the source directory, if a destination file already exists,
its h1 text is saved and restored into the newly copied template.
"""

import os
import shutil

from bs4 import BeautifulSoup

SRC = "/custom_html"
DST = "/vol/web/nginx/data"


def copy_with_preserved_h1(src: str, dst: str) -> None:
    """
    Zkopíruje HTML šablony ze zdrojového adresáře do cílového, přičemž zachová obsah elementu h1.

    Pro každý HTML soubor ve zdrojovém adresáři: pokud cílový soubor existuje,
    uloží se text jeho h1 a po zkopírování nové šablony se obnoví.

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

            # Save existing h1 content if destination exists
            h1_text = None
            if os.path.exists(dst_file):
                with open(dst_file) as fp:
                    soup = BeautifulSoup(fp, "html.parser")
                    h1 = soup.find("h1")
                    if h1 and h1.string:
                        h1_text = str(h1.string)

            # Copy new template (overwrite)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)

            # Restore h1 content if it was saved
            if h1_text is not None:
                with open(dst_file) as fp:
                    soup = BeautifulSoup(fp, "html.parser")
                h1 = soup.find("h1")
                if h1:
                    h1.string.replace_with(h1_text)
                with open(dst_file, "w") as fp:
                    fp.write(str(soup))


if __name__ == "__main__":
    copy_with_preserved_h1(SRC, DST)
