#!/usr/bin/env python3
"""Upozornění na chybějící/nesprávné docstringy metod podle projektového style guide."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

IGNORED_FILE_PATH_PARTS = {"migrations"}
IGNORED_CLASS_NAMES = {"Meta"}
IGNORED_METHOD_NAMES = {"__str__", "__repr__"}


def should_bypass_exclusions() -> bool:
    value = os.getenv("DOCSTRING_CHECK_BYPASS_EXCLUSIONS", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def should_check_file(path: Path, bypass_exclusions: bool) -> bool:
    if bypass_exclusions:
        return True

    path_parts = set(path.parts)
    return not bool(path_parts & IGNORED_FILE_PATH_PARTS)


class MethodDocstringChecker(ast.NodeVisitor):
    def __init__(self, file_path: Path, bypass_exclusions: bool = False) -> None:
        self.file_path = file_path
        self.bypass_exclusions = bypass_exclusions
        self.class_stack: list[str] = []
        self.function_depth = 0
        self.warnings: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._check_class(node)
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function_like(node)
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function_like(node)
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def _check_class(self, node: ast.ClassDef) -> None:
        if not self.bypass_exclusions:
            if node.name in IGNORED_CLASS_NAMES:
                return

            if node.name.startswith("_") and not node.name.startswith("__"):
                return

        location = f"{self.file_path}:{node.lineno}"
        qualified_name = f"{'.'.join(self.class_stack + [node.name])}"
        self._check_docstring(node, "třídy", qualified_name, location, args=[])

    def _check_function_like(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if self.function_depth > 0:
            return

        function_name = node.name
        args = [arg.arg for arg in node.args.args if arg.arg not in {"self", "cls"}]
        location = f"{self.file_path}:{node.lineno}"
        if self.class_stack:
            if not self.bypass_exclusions:
                if function_name in IGNORED_METHOD_NAMES:
                    return

                if function_name.startswith("_") and not function_name.startswith("__"):
                    return

            qualified_name = f"{'.'.join(self.class_stack)}.{function_name}"
            self._check_docstring(node, "metody", qualified_name, location, args=args)
            return

        if not self.bypass_exclusions and function_name.startswith("_") and not function_name.startswith("__"):
            return

        self._check_docstring(node, "funkce", function_name, location, args=args)

    def _check_docstring(
        self,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        element_type: str,
        qualified_name: str,
        location: str,
        args: list[str],
    ) -> None:
        docstring = ast.get_docstring(node)
        if not docstring:
            self.warnings.append(f"{location}: WARNING DOC001 Chybí docstring {element_type} '{qualified_name}'.")
            return

        lines = [line for line in docstring.splitlines() if line.strip()]
        if not lines:
            self.warnings.append(f"{location}: WARNING DOC002 Prázdný docstring {element_type} '{qualified_name}'.")
            return

        if len(lines[0].split()) < 3:
            self.warnings.append(f"{location}: WARNING DOC003 Shrnutí je příliš krátké u {element_type} '{qualified_name}'.")

        for arg in args:
            if f":param {arg}:" not in docstring:
                self.warnings.append(f"{location}: WARNING DOC004 Chybí ':param {arg}:' u {element_type} '{qualified_name}'.")

        has_return_annotation = getattr(node, "returns", None) is not None
        if has_return_annotation and ":return:" not in docstring and ":returns:" not in docstring:
            self.warnings.append(f"{location}: WARNING DOC005 Chybí ':return:' u {element_type} '{qualified_name}'.")


def iter_python_files(paths: list[str]) -> list[Path]:
    candidates = [Path(path) for path in paths if path.endswith(".py")]
    bypass_exclusions = should_bypass_exclusions()
    return [path for path in candidates if path.exists() and path.is_file() and should_check_file(path, bypass_exclusions)]


def main() -> int:
    bypass_exclusions = should_bypass_exclusions()
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

        checker = MethodDocstringChecker(file_path, bypass_exclusions=bypass_exclusions)
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
