# AIS CR ecosystem map

<!-- delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00 -->

Canonical human-readable list of the AIS CR repositories managed by sync policy: which owns which subject area, and what each is built on.

**How to use:** Load this file to route work to the owning repository or set per-stack expectations — for example API doc alignment, governance bootstrap, or sibling delivery.
The table is the payload, identical in every repository that receives it.

**Maintenance:** the map is refreshed at the management hub against its machine registry by the `aiscr-write-ecosystem-map` workflow, owner of the procedure and the registry-agreement rule.
Do not add or remove rows in a repository that does not carry that registry.

**OpenSpec posture is not a column here.**
Each repository declares its own posture locally, in the `context:` content of its OpenSpec configuration, and that local declaration is what a session running in the repository reads.
The `sync registry` column records whether a repository is a delivery target of the management hub; the hub is the delivery source and is not a target of itself.

| Repo | Type | Purpose | sync registry | GitHub (ARUP-CAS) |
|------|------|---------|---------------|-------------------|
| aiscr-management | management | Governance and workflow-authoring hub: canonical AI config, workflow bodies, sibling delivery; no task-based review | n/a — delivery source | [aiscr-management](https://github.com/ARUP-CAS/aiscr-management) |
| aiscr-webamcr | webapp | Python/Django webapp | yes | [aiscr-webamcr](https://github.com/ARUP-CAS/aiscr-webamcr) |
| aiscr-digiarchiv-2 | webapp | Java + Angular | yes | [aiscr-digiarchiv-2](https://github.com/ARUP-CAS/aiscr-digiarchiv-2) |
| aiscr-webamcr-help | docs | User documentation, Quarto / R | yes | [aiscr-webamcr-help](https://github.com/ARUP-CAS/aiscr-webamcr-help) |
| aiscr-api-home | docs | API documentation, Quarto | yes | [aiscr-api-home](https://github.com/ARUP-CAS/aiscr-api-home) |
| aiscr-oao | docs | Data presentation, R / Shiny | yes | [aiscr-oao](https://github.com/ARUP-CAS/aiscr-oao) |
| aiscr-amcr-home | web | Svelte / frontend | yes | [aiscr-amcr-home](https://github.com/ARUP-CAS/aiscr-amcr-home) |
| aiscr-home | web | Svelte / frontend | yes | [aiscr-home](https://github.com/ARUP-CAS/aiscr-home) |
| aiscr-rdf-vocabs | docs | RDF vocabularies | yes | [aiscr-rdf-vocabs](https://github.com/ARUP-CAS/aiscr-rdf-vocabs) |
| aiscr-docs-pipeline | service | Document processing pipeline: orchestration, service deployment, trust gate | yes | [aiscr-docs-pipeline](https://github.com/ARUP-CAS/aiscr-docs-pipeline) |
| aiscr-news | web | Shared news feed for the AIS CR sites, Node / GitHub Pages | yes | [aiscr-news](https://github.com/ARUP-CAS/aiscr-news) |
| aiscr-qgis-amcr-viewer | plugin | QGIS plugin for AMČR Digital Archive data, Python | yes | [aiscr-qgis-amcr-viewer](https://github.com/ARUP-CAS/aiscr-qgis-amcr-viewer) |
| aiscr-qgis-pian-exporter | plugin | QGIS plugin preparing spatial data for AMČR imports, Python | yes | [aiscr-qgis-pian-exporter](https://github.com/ARUP-CAS/aiscr-qgis-pian-exporter) |
| aiscr-gis-convert | webapp | GIS data converter for AMČR, Node / React | yes | [aiscr-gis-convert](https://github.com/ARUP-CAS/aiscr-gis-convert) |
| aiscr-cva-annotation-game | webapp | Archaeotag crowdsourced photo annotation, SvelteKit / PostgreSQL | yes | [aiscr-cva-annotation-game](https://github.com/ARUP-CAS/aiscr-cva-annotation-game) |
| aiscr-aonline | webapp | Archeologie online, Java / Solr | yes | [aiscr-aonline](https://github.com/ARUP-CAS/aiscr-aonline) |
| aiscr-atr | service | Automatic text recognition (OCR/HTR) service | yes | [aiscr-atr](https://github.com/ARUP-CAS/aiscr-atr) |
| aiscr-detect-artefact | service | Artefact detection in photos (computer vision) service | yes | [aiscr-detect-artefact](https://github.com/ARUP-CAS/aiscr-detect-artefact) |

## Type definitions

- **management** — Governance and workflow-authoring control plane; canonical AI config, workflow bodies, and sibling-delivery tooling; no task-based review. **webapp** — Backend/frontend application (e.g.
  Django, Java/Angular). **docs** — Documentation or data-publication site: user and API documentation, data presentations, vocabularies (e.g.
  Quarto, R/Shiny, RDF on GitHub Pages). **web** — Frontend or marketing site, or content published for the AIS CR sites (e.g.
  SvelteKit, a GitHub Pages feed). **service** — Processing services, ML inference and orchestration, with their deployment; no end-user UI. **plugin** — Desktop plugin for a host application (e.g.
  QGIS), released through that application's plugin channel.
