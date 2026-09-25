# Implementation plan — Versioned Rosetta catalogs

## Outcome

Make the repository the authoritative source of the Czech and English
translation catalogs.  A deployment must seed the runtime `locale_data`
volume from the image, add source-code message IDs, compile `.mo` files, and
then expose only the volume catalogs to Rosetta.  The existing maintenance
message becomes database data, not a catalog entry.

## Decisions fixed by this plan

- Version only `locale/cs/LC_MESSAGES/django.po` and
  `locale/en/LC_MESSAGES/django.po` at the repository root.  Keep `*.mo` and
  `*.pot` ignored.
- Copy those files into the production image at `/default_locale`, outside
  `/code` and outside `LOCALE_PATHS`.  This prevents Rosetta from discovering
  the immutable image catalog in addition to `/vol/web/locale`.
- At application start, stage the default catalog in `/code/locale`, run
  `makemessages` and `compilemessages` there, copy the resulting `.po` and
  `.mo` to the volume, and remove the staging files.  Thus Rosetta sees only
  the runtime volume catalog.
- Before replacing an existing volume catalog, create a timestamped
  `django_backup_*.po` copy in `$HOME/translations_backup/<language>/LC_MESSAGES`.
  Mount this existing host directory in the web service at `/backup`; a
  minute-based sidecar sync alone cannot prove that a backup occurred before
  the overwrite.
- Store maintenance body text in `OdstavkaSystemu.text_cs` and
  `OdstavkaSystemu.text_en` as blank-allowed `TextField`s.  Render the field
  selected by the active language in `base.html`; do not use gettext for this
  operational data.

## Implementation steps

1. Obtain the current reviewed `django.po` files from the production volume
   (or Rosetta download) for `cs` and `en`.  Validate both with gettext/polib,
   place them in the two repository paths above, and inspect the staged diff.
   Do not manufacture an empty catalog: the purpose of this change is to
   preserve the approved current translations as the initial baseline.

2. Update `Dockerfile` to copy the root `locale/` directory to
   `/default_locale` after the runtime user exists, with read access for the
   application user.  Retain `/vol/web/locale` as the runtime mount point.
   Do not put the tracked catalogs at `/code/locale`, because
   `find_pos_with_backup()` searches that directory as well as
   `settings.LOCALE_PATHS` and would expose duplicates in Rosetta.

3. Replace the locale section of `scripts/entrypoint.sh` with a strict,
   quoted shell workflow for each language in `cs en`:

   - Create `/vol/web/locale/<lang>/LC_MESSAGES`, the matching backup
     directory below `/backup`, and the temporary `/code/locale` directory.
   - Verify that `/default_locale/<lang>/LC_MESSAGES/django.po` exists and
     that `/backup` is writable when a volume catalog already exists; fail the
     deployment before changing the volume if either invariant is false.
   - If a volume `django.po` exists, copy it to
     `/backup/<lang>/LC_MESSAGES/django_backup_<UTC timestamp>.po` before any
     replacement.  Use a timestamp with seconds (or greater precision) so a
     simultaneous Czech/English deployment cannot collide.  This naming also
     remains discoverable by the existing Rosetta backup code.
   - Copy the image baseline to the temporary `/code/locale` catalog, run
     `python3 manage.py makemessages -l <lang>`, then
     `python3 manage.py compilemessages -l <lang>`.
   - Copy the generated `django.po` and `django.mo` to the volume using a
     temporary target plus `mv` for each file, so readers do not observe a
     partially written catalog.  Remove only the temporary `/code/locale`
     files afterward.  Do not delete Rosetta-created backup files on the
     volume.

   Avoid `eval`, unquoted glob copies, and a blanket `rm`; the present block
   uses all three and is fragile with missing files.  `set -e` must propagate
   failed extraction, compilation, copying, or backup operations.

4. Make the pre-overwrite backup available in every production-like compose
   definition that invokes `scripts/entrypoint.sh`: `docker-compose.yml`,
   `docker-compose-test.yml`, and `git_docker-compose.yml`.  Add the same
   `$HOME/translations_backup:/backup` bind mount to `web` that the sidecar
   already has.  Ensure the deployment scripts create the host directory with
   permissions writable by the container's `user`; add the equivalent setup to
   `scripts/git_prod_deploy.sh`, which currently has neither a sidecar nor a
   backup-directory setup.  Development compose files use `entrypoint.dev.sh`
   and are not part of this startup workflow.

5. Add `text_cs` and `text_en` to `OdstavkaSystemu` in `core/models.py` and
   create the next normal Django migration.  Include both fields in
   `OdstavkaSystemuForm.Meta.fields`, remove the custom initialization that
   reads `django.po`, and leave the existing custom 503 HTML fields/handling
   unchanged.  Simplify `OdstavkaSystemuAdmin.save_model()` so it saves the
   model and 503 HTML changes, clears the `maintenance` cache, and performs no
   `polib`, `.po`, `.mo`, or translation-reload work.  Remove now-unused
   `settings`, `pofile`, and any related imports.

6. Change the maintenance banner in `webclient/templates/base.html` to render
   `action.text_en` for English and `action.text_cs` otherwise.  It must retain
   Django template auto-escaping.  This template change is required: changing
   the form and model alone would leave `{% trans "base.odstavka.text" %}` as
   the displayed value.

7. Plan the data cutover explicitly.  A schema migration cannot read the old
   production-only `.po` volume, so it cannot faithfully migrate the active
   maintenance message.  Immediately before the first rollout, record the two
   current `base.odstavka.text` values from the backed-up catalogs; after the
   schema migration and before enabling traffic, save those values into the
   existing `OdstavkaSystemu` row through the admin (or a reviewed one-off,
   environment-specific operation).  Verify the rendered Czech and English
   banners.  Do not encode production text in a reusable migration.

8. Rewrite `docs/source/06_funkcionalita/preklady.rst` to state that Git is the
   source of truth, explain that Rosetta edits survive only until deployment,
   and document the exact edit → download `django.po` → replace the matching
   root `locale/.../django.po` → validate → code-review/commit loop.  Document
   that `.mo` files and Rosetta `django_backup_*.po` files remain runtime-only,
   and that the sidecar plus pre-overwrite copy are recovery mechanisms rather
   than authoritative storage.

## Tests and verification

- Add focused tests in a new small core test module (rather than Selenium):
  model/form tests prove `text_cs` and `text_en` persist, the form no longer
  opens or parses a catalog, and saving an outage does not call `polib` or
  write `.po`/`.mo`.  Render `base.html` under Czech and English language
  overrides with an active maintenance object and assert the corresponding
  text is present and the other is absent/unused.
- Add shell-level integration coverage (or a repeatable CI verification
  script) with temporary image/volume/backup paths: start with an empty volume
  and assert both default `.po` files and compiled `.mo` files exist; start
  with sentinel volume translations and assert they are replaced by the image
  baseline while a timestamped backup retains the sentinel; add a temporary
  source gettext key and assert `makemessages` adds it to the runtime `.po`.
- Build the production image and inspect it: `/default_locale` contains only
  tracked `.po` files; no repository `.mo` is present.  Run
  `git ls-files 'locale/**/*.po'`, `git ls-files '*.mo'`, `git check-ignore`
  for a candidate `.mo`, `manage.py makemigrations --check`, the targeted core
  tests, `python -m compileall -q webclient`, and `pre-commit run --all-files`.
- Run the relevant compose configuration validation (`docker compose config`
  or the repository's deployment equivalent) and perform a staging deployment.
  Confirm Rosetta lists one main catalog per language, app strings translate
  without an editor save, new IDs appear in the volume catalog, and a Rosetta
  edit is intentionally reverted by the next deployment unless committed.

## Delivery order

1. Baseline catalog export and review.
2. Image/entrypoint/compose backup mechanics, verified with throwaway volumes.
3. Maintenance schema, UI, and tests.
4. Documentation and staging cutover rehearsal.
5. Production rollout with the explicit maintenance-text transfer and backup
   verification.

The expected change spans the two new `.po` files, `Dockerfile`, the three
production-like compose files, the Mac/local development compose files,
`scripts/entrypoint.sh`, `scripts/entrypoint.dev.sh`,
`scripts/git_prod_deploy.sh`, the core model/form/admin/template/migration and
tests, plus `docs/source/06_funkcionalita/preklady.rst`.
