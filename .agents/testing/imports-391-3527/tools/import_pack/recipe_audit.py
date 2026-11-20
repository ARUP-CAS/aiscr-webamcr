"""Mechanická kontrola vygenerovaných vstupů proti inventáři mapperů a modelů aplikace."""

import re

LOOKUP = re.compile(r"LookupImportField\(\s*(\w+)")
FAMILY = re.compile(r"'nazev_heslare':\s*(HESLAR_\w+)")


def _empty(value):
    return value is None or str(value).strip() == ""


def _lookup_target(definition):
    """
    Vrátí cílový model a případnou rodinu hesláře z textu definice ``LookupImportField``.

    :param definition: Zdrojový výraz pole z inventáře.
    :return: Dvojice (název modelu, název konstanty ``HESLAR_*`` nebo ``None``), nebo ``(None, None)``.
    """
    model = LOOKUP.search(definition or "")
    family = FAMILY.search(definition or "")
    return (model.group(1) if model else None), (family.group(1) if family else None)


def _identity_models(inventory, model):
    """
    Vrátí modely, které sdílejí identifikátor záznamu přes primární klíč ``OneToOneField`` v libovolném směru.

    Například ``Akce`` má primární klíč na ``ArcheologickyZaznam``, takže ``ident_cely`` jedné akce je platnou
    hodnotou vyhledávání v obou modelech; totéž platí pro ``NeidentAkce`` a ``DokumentCast``.

    :param inventory: Zmrazený inventář zdroje.
    :param model: Název modelu odkazované třídy.
    :return: Množina názvů modelů včetně ``model``.
    """
    edges = {}
    for name, definition in inventory["models"].items():
        for info in definition.get("fields", {}).values():
            if info.get("type") == "OneToOneField" and info.get("primary_key") and info.get("args"):
                parent = info["args"][0].get("expression")
                edges.setdefault(name, set()).add(parent)
                edges.setdefault(parent, set()).add(name)
    names, pending = {model}, [model]
    while pending:
        for other in edges.get(pending.pop(), ()):
            if other not in names:
                names.add(other)
                pending.append(other)
    return names


def audit_rows(inventory, batches):
    """
    Zkontroluje řádky vložení s očekávaným výsledkem ``apply`` proti povinnosti a cíli polí v inventáři.

    Hlásí povinný sloupec s prázdnou hodnotou, syntetický identifikátor záznamu jiného modelu, než jaký
    pole vyhledává,
    a odkaz ``$ref:HESLAR_*`` nebo pevné heslo mimo vyžadovanou rodinu hesláře. Hodnoty ``$ref`` bez rodiny
    (katastr, mapové listy apod.) se nedají ověřit staticky a hlásí se odděleně jako neověřené.

    :param inventory: Zmrazený inventář zdroje (``mappers``, ``models``).
    :param batches: Dávky manifestu; kontrolují se jen ``insert`` s ``expected == "apply"``.
    :return: Slovník se seznamy ``findings`` a ``unchecked``.
    """
    mappers = {m["csv"].removesuffix(".csv"): m for m in inventory["mappers"]}
    owners = {
        str(row["ident_cely"]): name
        for batch in batches
        for name, rows in batch["tables"].items()
        for row in rows
        if row.get("ident_cely") and not str(row["ident_cely"]).startswith("$")
    }
    findings, unchecked = [], set()
    for batch in batches:
        if batch.get("operation") != "insert" or batch.get("expected") != "apply":
            continue
        for name, rows in batch["tables"].items():
            mapper = mappers.get(name)
            if mapper is None:
                continue
            for index, row in enumerate(rows, 1):
                where = f"{batch['id']}/{name}#{index}"
                for column, info in mapper["columns"].items():
                    value = row.get(column)
                    if info["kind"] in ("model", "lookup") and not info.get("nullable", True):
                        if column in row and _empty(value):
                            findings.append({"at": where, "column": column, "problem": "required value is empty"})
                    if info["kind"] != "lookup" or _empty(value):
                        continue
                    target, family = _lookup_target(info.get("definition"))
                    if target not in inventory["models"]:
                        # Custom lookups (vazba owners, user keys) resolve dynamically; vazba is covered
                        # by the known-defect classifier, not by this static check.
                        continue
                    text = str(value)
                    if text in owners:
                        referenced = mappers.get(owners[text])
                        if referenced and target not in _identity_models(inventory, referenced["model"]):
                            findings.append(
                                {
                                    "at": where,
                                    "column": column,
                                    "problem": f"row of {referenced['model']} used for lookup in {target}",
                                }
                            )
                    elif text.startswith("$ref:HESLAR_"):
                        if target != "Heslar" or (family and text[5:] != family):
                            findings.append(
                                {
                                    "at": where,
                                    "column": column,
                                    "problem": f"{text[5:]} used for lookup in {target} {family or ''}".strip(),
                                }
                            )
                    elif text.startswith("$ref:"):
                        unchecked.add(f"{name}.{column}={text}")
    return {"findings": findings, "unchecked": sorted(unchecked)}


def unique_keys(inventory, model):
    """
    Vrátí unikátní kombinace polí modelu z inventáře (``unique_together`` i ``UniqueConstraint``).

    :param inventory: Zmrazený inventář zdroje.
    :param model: Název modelu.
    :return: Seznam n-tic názvů polí.
    """
    import ast

    keys = []
    for text in inventory["models"].get(model, {}).get("constraints", []) or []:
        text = str(text)
        if text.startswith("(("):
            try:
                keys += [tuple(group) for group in ast.literal_eval(text)]
            except (ValueError, SyntaxError):
                continue
        for match in re.finditer(r"UniqueConstraint\(fields=\[([^\]]+)\]", text):
            keys.append(tuple(part.strip().strip("'\"") for part in match.group(1).split(",")))
    return keys


def audit_uniqueness(inventory, batches):
    """
    Najde řádky vložení s očekávaným výsledkem ``apply``, které by porušily unikátní omezení modelu.

    Porovnává všechna apply-insert vložení napříč dávkami, protože i řádek z dřívější dávky už v DB existuje.

    :param inventory: Zmrazený inventář zdroje.
    :param batches: Dávky manifestu.
    :return: Seznam nálezů ``{"class", "fields", "value", "rows"}``.
    """
    mappers = {m["csv"].removesuffix(".csv"): m for m in inventory["mappers"]}
    seen, findings = {}, []
    for batch in batches:
        if batch.get("operation") != "insert" or batch.get("expected") != "apply":
            continue
        for name, rows in batch["tables"].items():
            mapper = mappers.get(name)
            if mapper is None:
                continue
            to_column = {info.get("model_field", column): column for column, info in mapper["columns"].items()}
            for fields in unique_keys(inventory, mapper["model"]):
                if not all(field in to_column for field in fields):
                    continue
                for index, row in enumerate(rows, 1):
                    value = tuple(str(row.get(to_column[field], "")) for field in fields)
                    if any(v == "" or v.startswith("$") for v in value):
                        continue
                    where = f"{batch['id']}/{name}#{index}"
                    key = (name, fields, value)
                    if key in seen:
                        findings.append(
                            {"class": name, "fields": list(fields), "value": list(value), "rows": [seen[key], where]}
                        )
                    else:
                        seen[key] = where
    return findings
