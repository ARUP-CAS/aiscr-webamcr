from pathlib import Path

from scripts.check_container_image_reference_parity import apply_compose_cross_fix


def _compose(*services):
    return {"services": {name: {"image": image} for name, image in services}}


def test_cross_fix_reports_missing_prod_literal_when_not_whitelisted():
    """Ověří chybu pro literální repo bez produkčního literálu i whitelistu."""
    consumer = _compose(("cadvisor", "gcr.io/cadvisor/cadvisor:v0.55.1"))

    errors, modified = apply_compose_cross_fix(
        consumer,
        Path("docker-compose-dev-local-db.yml"),
        {},
        {},
        fix=False,
        verbose=False,
    )

    assert modified is False
    assert len(errors) == 1
    assert "whitelist" in errors[0]
    assert "gcr.io/cadvisor/cadvisor" in errors[0]


def test_cross_fix_allows_whitelisted_dev_only_repo():
    """Potvrdí, že explicitně whitelisted dev-only repo nevrací chybu."""
    consumer = _compose(("pgadmin", "dpage/pgadmin4:latest"))

    errors, modified = apply_compose_cross_fix(
        consumer,
        Path("docker-compose-dev-local-db-all-containers.yml"),
        {},
        {},
        fix=False,
        verbose=False,
    )

    assert errors == []
    assert modified is False


def test_cross_fix_updates_mismatched_repo_present_in_prod():
    """Při fix režimu přepíše pin na produkční referenci, pokud repo existuje v prod."""
    consumer = _compose(("grafana", "grafana/grafana-enterprise:11.0.0"))
    prod_map = {"grafana/grafana-enterprise": "grafana/grafana-enterprise:12.4.2"}

    errors, modified = apply_compose_cross_fix(
        consumer,
        Path("docker-compose-dev-local-db.yml"),
        prod_map,
        {},
        fix=True,
        verbose=False,
    )

    assert errors == []
    assert modified is True
    assert consumer["services"]["grafana"]["image"] == "grafana/grafana-enterprise:12.4.2"


def test_cross_fix_skips_non_literal_images_without_error():
    """Neliterální image musí zůstat mimo cross-file porovnání bez falešné chyby."""
    consumer = _compose(("web", "${amcr_image}"), ("redis", "redis:8.4.0"))
    prod_map = {"redis": "redis:8.4.0"}

    errors, modified = apply_compose_cross_fix(
        consumer,
        Path("docker-compose-dev-local-db.yml"),
        prod_map,
        {},
        fix=False,
        verbose=False,
    )

    assert errors == []
    assert modified is False


def test_cross_fix_deduplicates_missing_prod_repo_errors():
    """Stejné chybějící repo v jednom consumer compose má být nahlášeno jen jednou."""
    consumer = _compose(
        ("cadvisor-a", "gcr.io/cadvisor/cadvisor:v0.55.1"),
        ("cadvisor-b", "gcr.io/cadvisor/cadvisor:v0.55.1"),
    )

    errors, modified = apply_compose_cross_fix(
        consumer,
        Path("docker-compose-dev-local-db.yml"),
        {},
        {},
        fix=False,
        verbose=False,
    )

    assert modified is False
    assert len(errors) == 1


def test_cross_fix_uses_dockerfile_source_for_repo_alignment():
    """Repo může být srovnáno podle lokálního Dockerfile zdroje pravdy."""
    consumer = _compose(("redis", "redis:8.4.0"))

    errors, modified = apply_compose_cross_fix(
        consumer,
        Path("docker-compose-dev-local-db.yml"),
        {},
        {"redis": "redis:8.4.0"},
        fix=False,
        verbose=False,
    )

    assert errors == []
    assert modified is False


def test_cross_fix_reports_dockerfile_source_drift():
    """Drift vůči Dockerfile source of truth musí vrátit chybu."""
    consumer = _compose(("redis", "redis:8.6.2"))

    errors, modified = apply_compose_cross_fix(
        consumer,
        Path("docker-compose-dev-local-db.yml"),
        {},
        {"redis": "redis:8.4.0"},
        fix=False,
        verbose=False,
    )

    assert modified is False
    assert len(errors) == 1
    assert "Dockerfile source" in errors[0]
