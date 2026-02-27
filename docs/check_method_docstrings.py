#!/usr/bin/env python3
"""Upozornění na chybějící/nesprávné docstringy metod podle projektového style guide."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

IGNORED_METHOD_NAMES = {"__str__", "__repr__"}


class MethodDocstringChecker(ast.NodeVisitor):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.class_stack: list[str] = []
        self.warnings: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function_like(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function_like(node)
        self.generic_visit(node)

    def _check_function_like(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if not self.class_stack:
            return

        method_name = node.name
        if method_name in IGNORED_METHOD_NAMES:
            return

        if method_name.startswith("_") and not method_name.startswith("__"):
            return

        args = [arg.arg for arg in node.args.args if arg.arg not in {"self", "cls"}]
        docstring = ast.get_docstring(node)
        location = f"{self.file_path}:{node.lineno}"
        qualified_name = f"{'.'.join(self.class_stack)}.{method_name}"

        if not docstring:
            self.warnings.append(f"{location}: WARNING DOC001 Chybí docstring metody '{qualified_name}'.")
            return

        lines = [line for line in docstring.splitlines() if line.strip()]
        if not lines:
            self.warnings.append(f"{location}: WARNING DOC002 Prázdný docstring metody '{qualified_name}'.")
            return

        if len(lines[0].split()) < 3:
            self.warnings.append(f"{location}: WARNING DOC003 Shrnutí je příliš krátké u metody '{qualified_name}'.")

        for arg in args:
            if f":param {arg}:" not in docstring:
                self.warnings.append(f"{location}: WARNING DOC004 Chybí ':param {arg}:' u metody '{qualified_name}'.")

        has_return_annotation = getattr(node, "returns", None) is not None
        if has_return_annotation and ":return:" not in docstring and ":returns:" not in docstring:
            self.warnings.append(f"{location}: WARNING DOC005 Chybí ':return:' u metody '{qualified_name}'.")


def iter_python_files(paths: list[str]) -> list[Path]:
    candidates = [Path(path) for path in paths if path.endswith(".py")]
    return [path for path in candidates if path.exists() and path.is_file()]


def main() -> int:
    files = iter_python_files(sys.argv[1:])
    if not files:
        return 0

    warnings: list[str] = []
    for file_path in files:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as exc:
            warnings.append(
                f"{file_path}:{exc.lineno}: WARNING DOC000 Soubor se nepodařilo zpracovat pro kontrolu docstringů: {exc.msg}"
            )
            continue

        checker = MethodDocstringChecker(file_path)
        checker.visit(tree)
        warnings.extend(checker.warnings)

    if warnings:
        print("Připomínka stylu docstringů (neblokující):")
        for warning in warnings:
            print(warning)
        print(
            "\nProsím upravte docstringy metod podle docs/source/04_django_aplikace/04_01_core/docstring_style_guide.rst"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
