"""Statický přehled mapperů, modelových polí a omezení bez spuštění Django."""

from __future__ import annotations

import ast
from pathlib import Path

from .common import SOURCE_HASH_MODE, source_digest


def literal(node):
    """Vrátí literál, nebo čitelný výraz; nic nevyhodnocuje."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return {"expression": ast.unparse(node)}


def attrs(node):
    """Vybere deklarované atributy třídy."""
    return {
        target.id: value.value
        for value in node.body
        if isinstance(value, ast.Assign)
        for target in value.targets
        if isinstance(target, ast.Name)
    }


def inventory(repo: Path) -> dict:
    """Vrátí přehled všech registrovaných CSV tříd a zdrojové otisky."""
    mapper_path = repo / "webclient/core/import_data_mappers.py"
    tree = ast.parse(mapper_path.read_text(encoding="utf-8"))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    models, hashes = {}, {}
    for path in sorted((repo / "webclient").glob("*/models.py")):
        content = path.read_bytes()
        hashes[path.relative_to(repo).as_posix()] = source_digest(content)
        for node in ast.parse(content).body:
            if not isinstance(node, ast.ClassDef):
                continue
            fields = {}
            table = None
            constraints = []
            for statement in node.body:
                if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call):
                    for target in statement.targets:
                        if isinstance(target, ast.Name) and ast.unparse(statement.value.func).endswith(
                            ("Field", "ForeignKey")
                        ):
                            fields[target.id] = {
                                "type": ast.unparse(statement.value.func).split(".")[-1],
                                "args": [literal(arg) for arg in statement.value.args],
                                **{kw.arg: literal(kw.value) for kw in statement.value.keywords if kw.arg},
                            }
                if isinstance(statement, ast.ClassDef) and statement.name == "Meta":
                    for key, value in attrs(statement).items():
                        if key == "db_table":
                            table = literal(value)
                        if key in ("constraints", "unique_together"):
                            constraints.append(ast.unparse(value))
            if fields or table:
                models[node.name] = {
                    "table": table,
                    "fields": fields,
                    "constraints": constraints,
                    "source": path.relative_to(repo).as_posix(),
                    "line": node.lineno,
                }

    def inherited(name, key, default=None):
        node = classes.get(name)
        if node is None:
            return default
        values = attrs(node)
        if key in values:
            return literal(values[key])
        for base in node.bases:
            result = inherited(ast.unparse(base), key, None)
            if result is not None:
                return result
        return default

    def columns(name):
        node = classes[name]
        result = {}
        for base in node.bases:
            if ast.unparse(base) in classes:
                result.update(columns(ast.unparse(base)))
        raw = inherited(name, "fields", [])
        if isinstance(raw, (tuple, list)):
            for field in raw:
                result[field[-1] if isinstance(field, (tuple, list)) else field] = {"kind": "model"}
        values = attrs(node)
        lookup = values.get("lookup_fields_mapping")
        if isinstance(lookup, ast.Dict):
            for key, value in zip(lookup.keys, lookup.values):
                result[literal(key)] = {"kind": "lookup", "definition": ast.unparse(value)}
        for method in node.body:
            if not isinstance(method, ast.FunctionDef) or method.name != "get_mapping":
                continue
            for item in ast.walk(method):
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                            result[target.slice.value] = {"kind": "lookup", "definition": ast.unparse(item.value)}
        return result

    mappers = []
    for name, node in classes.items():
        registered = [
            literal(dec.args[0])
            for dec in node.decorator_list
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "register"
        ]
        if not registered:
            continue
        model = inherited(name, "model_class", {})
        model_name = model.get("expression") if isinstance(model, dict) else model
        key = inherited(name, "primary_key", "ident_cely")
        mapping = columns(name)
        if name in ("DistribuceMapper", "ParadataMapper"):
            mapping = {
                field: {"kind": "binary"}
                for field in ("path" if name == "ParadataMapper" else "id", "nazev", "mimetype", "distribution")
            }
        if name in ("UzivatelOpravneniMapper", "UzivatelNotifikaceMapper"):
            mapping = {field: {"kind": "lookup"} for field in key}
        owners = {}
        class_values = attrs(node).get("classes")
        aliases = {}
        if isinstance(class_values, (ast.Tuple, ast.List)):
            aliases = {literal(entry.elts[0]): ast.unparse(entry.elts[1]) for entry in class_values.elts}
        for item in inherited(name, "fields", []):
            if isinstance(item, (tuple, list)):
                owners[item[-1]] = aliases.get(item[0], model_name)
        rename = inherited(name, "column_to_field_mapping", {})
        for field, info in mapping.items():
            owner = owners.get(field, model_name)
            model_field = rename.get(field, field) if isinstance(rename, dict) else field
            info.update(model=owner, model_field=model_field)
            model_info = models.get(owner, {}).get("fields", {}).get(model_field, {})
            info["nullable"] = bool(model_info.get("null"))
        for field in key if isinstance(key, (list, tuple)) else [key]:
            mapping.setdefault(field, {"kind": "key"})
        mappers.append(
            {
                "csv": registered[0],
                "class": name,
                "model": model_name,
                "key": key,
                "prefix": inherited(name, "primary_key_prefix"),
                "allow_update": inherited(name, "allow_update", True),
                "columns": mapping,
                "line": node.lineno,
                "special_methods": [x.name for x in node.body if isinstance(x, ast.FunctionDef)],
            }
        )
    hashes[mapper_path.relative_to(repo).as_posix()] = source_digest(mapper_path.read_bytes())
    for rel in [
        "webclient/cron/tasks.py",
        "webclient/core/admin_sites.py",
        "webclient/core/views.py",
        "locale/cs/LC_MESSAGES/django.po",
        "locale/en/LC_MESSAGES/django.po",
        "webclient/core/distribution_names.py",
        "webclient/core/ident_cely.py",
        "webclient/core/management/commands/backfill_thumb_history.py",
        "webclient/core/repository_connector.py",
    ]:
        hashes[rel] = source_digest((repo / rel).read_bytes())
    constants_path = repo / "webclient/heslar/hesla.py"
    constants = {
        n.target.id: literal(n.value)
        for n in ast.parse(constants_path.read_text(encoding="utf-8")).body
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id.startswith("HESLAR_")
    }
    hashes[constants_path.relative_to(repo).as_posix()] = source_digest(constants_path.read_bytes())
    import subprocess

    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    identifiers = ast.parse((repo / "webclient/core/ident_cely.py").read_text(encoding="utf-8"))
    resolver = next(n for n in identifiers.body if isinstance(n, ast.FunctionDef) and n.name == "get_record_from_ident")
    patterns = sorted(
        {
            n.args[0].value
            for n in ast.walk(resolver)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "fullmatch"
            and n.args
            and isinstance(n.args[0], ast.Constant)
        }
    )
    return {
        "schema_version": 1,
        "source_commit": revision,
        "source_hash_mode": SOURCE_HASH_MODE,
        "source_hashes": hashes,
        "mappers": mappers,
        "models": models,
        "identifier_patterns": patterns,
        "vocabulary_constants": constants,
        "summary": {"classes": len(mappers), "update_allowed": sum(bool(x["allow_update"]) for x in mappers)},
    }
