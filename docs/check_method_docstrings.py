#!/usr/bin/env python3
"""
Kontrola docstringů tříd, metod a funkcí dle projektového style guide.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Set, Union

sys.stdout.reconfigure(encoding="utf-8")

# =========================
# Configuration
# =========================

IGNORED_DIRS = {
    "migrations",
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "static",
    "media",
}
IGNORED_CLASS_NAMES = {"Meta"}
IGNORED_METHOD_NAMES = {"__str__", "__repr__", "__init__", "__len__"}

DOC_PARSE_ERROR = "DOC000"
DOC_MISSING = "DOC001"
DOC_EMPTY = "DOC002"
DOC_SHORT_SUMMARY = "DOC003"
DOC_MISSING_PARAM = "DOC004"
DOC_MISSING_RETURN = "DOC005"

MIN_SUMMARY_WORDS = 3

# =========================
# Helpers
# =========================


def env_flag(name: str, default: str = "false") -> bool:
    """Vyhodnotí hodnotu proměnné prostředí jako booleovský příznak.

    :param name: Název proměnné prostředí.
    :param default: Výchozí hodnota použitá při neexistenci proměnné.
    :return: ```True```, pokud hodnota odpovídá pravdivému příznaku.
    """
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


# =========================
# File selection
# =========================


def iter_python_files(paths: list[str], bypass_exclusions: bool) -> Iterable[Path]:
    """Iteruje Python soubory ve vstupních cestách.

    :param paths: Seznam souborů nebo adresářů ke kontrole.
    :param bypass_exclusions: Pokud ``True``, nepoužije se filtr ignorovaných adresářů.
    :return: Generátor cest k nalezeným ```.py``` souborům.
    """
    for path_str in paths:
        path = Path(path_str)

        if path.is_file() and path.suffix == ".py":
            yield path
            continue

        if path.is_dir():
            for root, dirs, files in os.walk(path):
                if not bypass_exclusions:
                    dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

                for file in files:
                    if file.endswith(".py"):
                        yield Path(root) / file


# =========================
# AST Checker
# =========================


class MethodDocstringChecker(ast.NodeVisitor):
    """AST návštěvník, který kontroluje přítomnost a kvalitu docstringů."""

    def __init__(self, file_path: Path, bypass_exclusions: bool = False) -> None:
        self.file_path = file_path
        self.bypass_exclusions = bypass_exclusions
        self.class_stack: list[str] = []
        self.function_depth = 0
        self.warnings: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Zkontroluje docstring třídy a navštíví její potomky.

        :param node: AST uzel definice třídy.
        """
        if self._should_skip(node.name, IGNORED_CLASS_NAMES):
            return

        qualified_name = ".".join(self.class_stack + [node.name])
        self._check_docstring(node, "třídy", qualified_name, node.lineno, [])

        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Zpracuje běžnou definici funkce nebo metody.

        :param node: AST uzel definice funkce.
        """
        self._handle_function_like(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Zpracuje asynchronní definici funkce nebo metody.

        :param node: AST uzel asynchronní definice funkce.
        """
        self._handle_function_like(node)

    def _handle_function_like(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        if self.function_depth > 0:
            self.generic_visit(node)
            return

        ignored = IGNORED_METHOD_NAMES if self.class_stack else set()
        if self._should_skip(node.name, ignored):
            return

        if self.class_stack:
            qualified_name = f"{'.'.join(self.class_stack)}.{node.name}"
            element_type = "metody"
        else:
            qualified_name = node.name
            element_type = "funkce"

        args = self._collect_args(node)
        self._check_docstring(node, element_type, qualified_name, node.lineno, args)

        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def _should_skip(self, name: str, ignored_set: Set[str]) -> bool:
        if self.bypass_exclusions:
            return False
        if name in ignored_set:
            return True
        return name.startswith("_") and not name.startswith("__")

    def _collect_args(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> list[str]:
        all_args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
        args = [a.arg for a in all_args if a.arg not in {"self", "cls"}]

        if node.args.vararg:
            args.append(node.args.vararg.arg)
        if node.args.kwarg:
            args.append(node.args.kwarg.arg)

        return args

    def _has_meaningful_return(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool:
        if node.returns is None:
            return False

        if isinstance(node.returns, ast.Constant) and node.returns.value is None:
            return False
        if isinstance(node.returns, ast.Name) and node.returns.id == "None":
            return False

        return True

    def _check_docstring(
        self,
        node: ast.AST,
        element_type: str,
        name: str,
        line: int,
        args: list[str],
    ) -> None:
        docstring = ast.get_docstring(node)
        loc = f"{self.file_path}:{line}"

        if not docstring:
            self.warnings.append(f"{loc}: WARNING {DOC_MISSING} Chybí docstring {element_type} '{name}'.")
            return

        lines = [line for line in docstring.splitlines() if line.strip()]
        if not lines:
            self.warnings.append(f"{loc}: WARNING {DOC_EMPTY} Prázdný docstring {element_type} '{name}'.")
            return

        if len(lines[0].split()) < MIN_SUMMARY_WORDS:
            self.warnings.append(
                f"{loc}: WARNING {DOC_SHORT_SUMMARY} Shrnutí je příliš krátké u {element_type} '{name}'."
            )

        compiled_patterns = {arg: re.compile(rf":param\s+(?:[^\s]+\s+)?{re.escape(arg)}\s*:") for arg in args}

        for arg, pattern in compiled_patterns.items():
            if not pattern.search(docstring):
                self.warnings.append(
                    f"{loc}: WARNING {DOC_MISSING_PARAM} Chybí ':param {arg}:' u {element_type} '{name}'."
                )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and self._has_meaningful_return(node):
            if ":return:" not in docstring and ":returns:" not in docstring:
                self.warnings.append(f"{loc}: WARNING {DOC_MISSING_RETURN} Chybí ':return:' u {element_type} '{name}'.")


# =========================
# Main
# =========================


def main() -> int:
    """Spustí kontrolu docstringů nad zadanými Python soubory.

    :return: Návratový kód procesu (0 při úspěchu, jinak 1 ve strict režimu).
    """
    bypass_exclusions = env_flag("DOCSTRING_CHECK_BYPASS_EXCLUSIONS")
    strict_mode = env_flag("DOCSTRING_CHECK_STRICT")

    input_paths = sys.argv[1:] if len(sys.argv) > 1 else ["."]
    files = list(iter_python_files(input_paths, bypass_exclusions))

    if not files:
        print("Nebyl nalezen žádný soubor ke kontrole.")
        return 0

    all_warnings: list[str] = []

    for file_path in files:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
            checker = MethodDocstringChecker(file_path, bypass_exclusions)
            checker.visit(tree)
            all_warnings.extend(checker.warnings)
        except SyntaxError as exc:
            all_warnings.append(f"{file_path}:{exc.lineno}: WARNING {DOC_PARSE_ERROR} Syntaktická chyba: {exc.msg}")
        except UnicodeDecodeError:
            all_warnings.append(f"{file_path}:0: WARNING {DOC_PARSE_ERROR} Chyba kódování (očekáváno UTF-8)")
        except Exception as exc:
            all_warnings.append(f"{file_path}:0: WARNING {DOC_PARSE_ERROR} Neočekávaná chyba: {exc}")

    if all_warnings:
        print("\n--- Připomínka stylu docstringů ---")
        for w in all_warnings:
            print(w)

        print(f"\nNalezeno {len(all_warnings)} nedostatků.")
        print("Prosím upravte docstringy dle dokumentace:")
        print("docs/source/04_django_aplikace/04_01_core/docstring_style_guide.rst")

        return 1 if strict_mode else 0

    print("✅ Všechny docstringy odpovídají standardu.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
