Ukládání souborů — file storage and enrichment contract
=======================================================

.. note::

   This page is written in English on purpose. It is a deliberate exception to the Czech
   documentation, at least for the time being. The contract is shared with the ATRIUM partners,
   and parts of it will be reused in the public File API documentation and in the AMČR help.

   It is working material. Each part carries its status: **Implemented** (in the code and
   verified), **Agreed** (settled, not yet implemented), **Proposed** (a recommendation still to be
   decided) or **Open**.

This page defines how AMČR stores files, their alternative distributions, paradata and the
per-document enrichment record, and how these are written into Fedora. It covers the storage
side of the ATRIUM text workflow (SSH Open Marketplace
`0xSpVP <https://marketplace.sshopencloud.eu/workflow/0xSpVP>`__). It builds on the mechanism of
`aiscr-webamcr#3527 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3527>`__ and
`aiscr-digiarchiv-2#693 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/693>`__.


How a record is stored
----------------------

**Implemented.** Every record is one Fedora *Archival Group*, stored as one OCFL object. Every
committed transaction creates one new version of that object.

- ``_create_container`` in ``core/repository_connector.py`` creates the record container
  ``rest/AMCR/record/{ident_cely}`` as a Fedora ``ArchivalGroup``. It holds the record metadata
  (``metadata``) and the files (``file/{file_id}/``). Each file container holds the original
  (``orig``), the thumbnails and the distributions with their paradata.
- AMČR writes inside Fedora transactions (the ``Atomic-ID`` header, ``fcr:tx``). A transaction
  commits as a single version, however many writes it holds.
- AMČR runs Fedora 6.5.1 with the default storage settings: ``fcrepo.autoversioning.enabled=true``
  (every commit is a new OCFL version), ``fcrepo.persistence.defaultDigestAlgorithm=sha512``, and
  ``ocfl-fs`` storage.
- Inside the OCFL object, a binary is four files: its content, its RDF description
  (``~fcr-desc.nt``), and a header JSON for each of the two under ``.fcrepo/``. A container is two
  files (``fcr-container.nt`` and its header). Each version rewrites the object's inventory, which
  lists every file across all versions.
- AMČR computes SHA-512 for every binary and sends it in the ``Digest`` header. Fedora stores it as
  ``premis:hasMessageDigest``.

**Consequence.** Writing is not cheap: the cost grows with the number of files changed and the
number of versions, not with the bytes. All writes are therefore planned around one transaction
per record per run (see `Write plan`_).

.. mermaid::
   :align: center

   flowchart TD
       R["record/{ident_cely}<br/>ArchivalGroup = one OCFL object"] --> M["metadata"]
       R --> ME["metadata-en"]
       R --> RP["paradata/metadata-en"]
       R --> F["file/{file_id}"]
       F --> O["orig"]
       F --> T["thumb · thumb-large"]
       F --> OF["orig-format"]
       F --> AT["atr/docproc-json · atr/teitok-xml"]
       F --> CV["cva/coco-json · cva/wadm"]
       F --> DJ["atrium/document-json"]
       F --> P["paradata/orig · paradata/{distribution}"]


Principles
----------

1. **AMČR is the only writer** (Agreed). Every write to Fedora runs in AMČR's own code, with
   AMČR's credentials. Processing services and workers hold no Fedora credentials; they return
   results, and AMČR stores them.
2. **Everything belonging to a file is stored under that file** (Implemented). Each result is a
   distribution of the file it was derived from.
3. **Every distribution has one paradata file** (Agreed), the record included.
4. **The per-document record is stored in full** (Agreed), as a distribution of its own.
5. **Persist only what is expensive or impossible to rebuild** (Agreed): output of GPUs, language
   models or external services, and anything a person reviewed. Cheap projections are not stored.
6. **Each record is written once per run** (Agreed), in one transaction.


Paths, names, history and access
--------------------------------

**Implemented** in `aiscr-webamcr#3527 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3527>`__
(`aiscr-webamcr#4197 <https://github.com/ARUP-CAS/aiscr-webamcr/pull/4197>`__) and
`aiscr-digiarchiv-2#693 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/693>`__, and
documented for users in
`aiscr-api-home#41 <https://github.com/ARUP-CAS/aiscr-api-home/pull/41>`__.

- **Paths.** A distribution is stored at ``…/file/{file_id}/{distribution}``, and its paradata at
  ``…/file/{file_id}/paradata/{distribution}``. The File API serves them at
  ``/id/{ident_cely}/file/{file_id}/{distribution}`` and
  ``/id/{ident_cely}/file/{file_id}/paradata[/{distribution}]``. The bare ``/paradata`` path serves
  the paradata of ``orig``.
- **Reserved names**, each with its whole subtree: ``orig``, ``paradata`` and ``thumb/page``. At the
  record root, ``ro-crate-metadata.json`` is reserved as well (Agreed; see `Record crate (RO-Crate)`_).
  ``thumb/page`` is reserved because the Digital Archive serves page thumbnails there: JPEG images of
  the pages, rendered by its ``ThumbnailsGenerator`` and kept on its own storage, not in Fedora.
- **Name rules** (``core/distribution_names.py``):

  - a name is normalised by trimming whitespace and leading and trailing ``/``;
  - empty, ``.`` and ``..`` segments are refused;
  - a name cannot be both a distribution and the parent of another distribution.

  The convention is ``{family}/{format}``, in lower case, joined by hyphens.
- **History.** ``DIST01``, ``DIST11`` and ``DIST10`` record an insert, an update and a delete, with
  the distribution name as the note. The available distributions are those with a ``DIST01`` and
  no later ``DIST10``. Thumbnails keep this history too; they are left out of the download
  selector only because they have their own endpoints. Every write sends
  ``Overwrite-Tombstone: true``.
- **Filename, MIME type and digest** come from each binary's ``fcr:metadata`` (``ebucore:filename``,
  ``ebucore:hasMimeType``, ``premis:hasMessageDigest``).
- **Access.** Distributions and paradata follow the access rules of the original. The small
  thumbnail stays public. A missing distribution returns ``404``, and the original's rate limit
  applies.


Distribution catalogue
----------------------

**Agreed** unless marked otherwise.

.. list-table::
   :header-rows: 1
   :widths: 22 18 30 30

   * - Distribution
     - MIME type
     - Produced by
     - Issues
   * - ``orig``
     - as uploaded
     - upload or import (Implemented)
     - —
   * - ``thumb``, ``thumb-large``
     - ``image/png``
     - AMČR, rendered as PNG at upload (Implemented)
     - `aiscr-webamcr#3527 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3527>`__
   * - ``orig-format``
     - ``text/csv``
     - AMČR: DROID's own CSV export for the file, hash set to SHA-512
     - `aiscr-webamcr#4038 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4038>`__
   * - ``atrium/document-json``
     - ``application/json``
     - the record level: built from ``atr/docproc-json`` by ocr-postprocess, then enriched by the
       later steps of the same run
     - `aiscr-webamcr#2590 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/2590>`__,
       `atrium-project#84 <https://github.com/ufal/atrium-project/issues/84>`__
   * - ``atr/docproc-json``
     - ``application/json``
     - the layout level, one per document: digital-convert's when no page needs ATR, otherwise
       the ATR's, run on the whole document; for the existing mass OCR, a one-off converter of its
       ALTO, replaced later by the HPC ATR run
     - `aiscr-docs-pipeline#17 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/17>`__
       (schema), `aiscr-atr#2 <https://github.com/ARUP-CAS/aiscr-atr/issues/2>`__,
       `aiscr-docs-pipeline#19 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/19>`__,
       `aiscr-webamcr#3529 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3529>`__
   * - ``atr/teitok-xml``
     - ``application/xml``
     - nlp-enrich
     - `aiscr-docs-pipeline#4 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/4>`__,
       `aiscr-digiarchiv-2#113 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/113>`__
       (the TEITOK view)
   * - ``cva/coco-json``
     - ``application/json``
     - vision-detect (ARÚB; family kept open)
     - `aiscr-webamcr#3583 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3583>`__
   * - ``cva/wadm``
     - ``application/ld+json``
     - AMČR, converted from ``cva/coco-json`` (family kept open)
     - `aiscr-webamcr#3583 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3583>`__

**Two levels** (Agreed, 11–17 November 2026). ``atr/docproc-json`` is the layout: the route of
every page of the original, and the blocks of each page with their type, position, reading order
and text. Digital-convert and the ATR write it in the same format, to one versioned schema kept
in ``aiscr-docs-pipeline`` under an ARUP-CAS identifier. ``atrium/document-json`` is built from it:
the text in lines, each linked to its block and stating its text source (text layer, ATR or
legacy OCR) and how precise its box is (measured, derived or absent), every page with its content
status, and the enrichment. The record carries no run data and no copy of the layout. All boxes,
in both, are on the displayed page: the CropBox after ``/Rotate``, origin at the top left, in
points × ``UserUnit``.

**No ALTO** (Agreed). ``atr/alto-xml`` is neither produced nor stored. The ATR recognises by
blocks and does not measure lines, so its ALTO would claim a precision it does not have. An ALTO
export can be built from ``atr/docproc-json`` if a consumer ever needs one.

Kept only in the record, with no file of their own:

- **page classification** (``page_categories``, ``pages[].category*``). Its results are already
  persisted in the record, and the Digital Archive reads them from there
  (`aiscr-digiarchiv-2#710 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/710>`__);
- **keywords**, in two kinds, both from keyword-extract: *controlled* keywords from the
  vocabularies (the ``enrichment`` block, with concept identifiers), and *uncontrolled*
  statistical keywords with method and score (the ``keywords`` block). The two kinds are never merged: every keyword states the method that produced
  it. The default statistical method is KeyBERT; YAKE and the legacy KER method stay selectable.
  Consumers decide how to use them: free keywords, schema.org ``keywords``, an
  evaluation baseline, candidates for new vocabulary terms;
- **line quality** (``lines[]`` with categories and scores, and the page summaries in
  ``pages[]``). No consumer reads a per-line table: the Digital Archive indexes page and file
  aggregates from the record, and the pipeline builds nlp-enrich's input table from the record
  in memory.

**Discovery reads the record** (Agreed). The Digital Archive indexes page classes, lemmas,
entities, both keyword kinds and quality from the record, which carries the same blocks for every
origin
(`aiscr-digiarchiv-2#710 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/710>`__,
`aiscr-digiarchiv-2#711 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/711>`__,
`aiscr-digiarchiv-2#714 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/714>`__). The
files serve download, reuse and the TEITOK view.

The ``atrium/`` family is reserved for the record, and ``atrium/document-json`` is its final name.
It matches the tools' ``.document.json`` files and the ``atrium_document`` schema.

*Considered and rejected:* a ``cva/pages-csv`` file for page classification, which duplicates the
record; a per-line quality table ``atr/lines-csv`` (``text/csv``), which duplicates the record's
lines and has no consumer (a human-readable table can be generated on demand if someone asks);
converting the DROID output into another format, which would add a conversion to maintain. The
name ``atr/stats-csv`` was used only on a temporary test fixture.


Inputs
------

**Agreed** as rules; the routing is built with the orchestration (Open).

- **Every accepted type.** Every file type AMČR accepts for upload is processed by the reader for
  its kind: born-digital documents by the born-digital converter, scans and images by the ATR,
  the existing mass-OCR ALTO through a one-off conversion into ``atr/docproc-json``. A type that
  no reader handles yet is listed as pending in the job report, with the reason; it is never
  forced through another route. The routing table lives with the orchestration in
  `ARUP-CAS/aiscr-docs-pipeline <https://github.com/ARUP-CAS/aiscr-docs-pipeline>`__.
- **OCR text layers are not trusted.** A text layer left in a PDF by an earlier OCR run is not
  reused: such documents are recognised again, so the text has a known origin. The layer stays in
  ``orig`` and can serve as a comparison.
- **Mixed documents.** Digital-convert gives every page a verdict. If any page needs ATR, the
  whole document goes through the ATR with those pages forced, and the record builder keeps the
  text-layer lines of the other pages, linked to the ATR's blocks. No page is dropped or sampled.
- **Signals, not gates.** Page classes and quality do not decide what is processed (see
  `Text quality`_).

*Considered and rejected:* a fixed list of formats, which silently skips any type added later;
trusting existing OCR layers, whose engine and quality are unknown.


Text quality
------------

**Agreed.** Everything that carries text is processed, and the quality classification is a signal
for the consumer, not a gate.

- **Process everything.** Mixed pages are processed too (photographs with captions, plans with
  legends, forms): the aim is a consistent result, and leaving something out is a deliberate cost.
  Only obvious junk is excluded: ``Trash`` and ``Empty`` lines are left out of the input of the
  language tools, and a page is skipped only when it has no scoreable text. Handwritten pages are
  flagged, not dropped. Every line keeps its category in the record.
- **Classify for the consumer.** The tools deliver raw aggregates per page (line counts per
  category, word shares, average quality, main language, in ``pages[]``). The file level is the
  word-weighted sum of its pages. Services (entity confidence, search ranking) and users (facets,
  filters) use the classification as they need.
- **Configure, do not reprocess.** AMČR and the Digital Archive index the aggregates and turn them
  into bands and verdicts with configurable thresholds at index time, so a threshold change needs
  no reprocessing. The same helper lists candidates for re-OCR. Default thresholds are calibrated
  on a human-graded sample of pages from the mass-OCR corpus.

*Considered and rejected:* page and file verdicts as a processing gate, which would drop
legitimate short text such as captions.


English metadata (``metadata-en``)
----------------------------------

**Agreed.** ``metadata-en`` is the English rendition of the record's metadata *as last archived*.
It is generated on each archiving, and it serves discovery and reuse only: the Digital Archive, the
OAI-PMH format ``oai_amcr_en`` and ARIADNE. AMČR itself does not use it. Only archived records are
published in the Digital Archive, so nothing that is published lacks it.

- **Built** from AMČR's own English labels for every vocabulary-backed field (``heslo_en`` and
  ``popis_en`` in the vocabularies, ``nazev_en`` for RÚIAN units). Only the free-text fields go to
  the translator, translated in place. AMČR owns the list of fields to translate and sends it
  with each request; the translator has no default list
  (`aiscr-webamcr#3570 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3570>`__). The list used
  is recorded in the paradata, without any field text.
- **Generated** asynchronously after archiving, in its own transaction. That adds one version per
  archiving event. Existing archived records get it in one planned bulk pass.
- **Stored** at ``rest/AMCR/record/{ident_cely}/metadata-en`` (``application/xml``), a sibling of
  ``metadata``. Its paradata is at ``rest/AMCR/record/{ident_cely}/paradata/metadata-en`` and
  records, among other things, the SHA-512 of the ``metadata`` it was built from.
- **History:** ``DIST01``/``DIST11`` with the note ``metadata-en``, in the record's history.
- **Access:** exactly the rules of ``metadata``, wherever it is served. Fields that are not
  translated are copied unchanged, so protected fields (``chranene_udaje``) are present: the
  Digital Archive indexes ``metadata-en`` through the same models and protection as ``metadata``,
  and ``oai_amcr_en``, the English interface and the ``/id`` redirect filter it alike.
- **Licence:** no licence is computed; see `Licences`_. The translation's components and their
  terms are in its paradata.
- **Consumed** by
  `aiscr-digiarchiv-2#496 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/496>`__.
- **Pilot scope:** the pilot translates ``metadata-en`` only, in the translator's ``replace`` mode;
  the AMČR 2.2 schema accepts that output and refuses ``append``. Translation of the full text is
  a later decision, and no translated-ALTO distribution is defined.

Any future record-level rendition follows the same pattern: a sibling of ``metadata``, with its
paradata under ``record/{ident_cely}/paradata/``.

*Considered and rejected:* translating on every metadata edit, which doubles the record's versions
for an asset that matters only once published; field translations kept in the database with a
generated view, which costs too much for the benefit; ``xml:lang`` inside ``metadata``, which would
break the services that parse AMČR XML.


Paradata
--------

**Agreed.** Every paradata file is JSON-LD (``application/ld+json``) following the RO-Crate
`Process Run Crate <https://w3id.org/ro/wfrun/process>`__ profile. Each event is one schema.org
``CreateAction``.

- ``instrument``: the ``SoftwareApplication`` with its ``version`` (required by RO-Crate 1.2), and
  for services the ``ContainerImage`` with its digest;
- ``object``: the inputs, named by distribution and SHA-512, with the record version read; an
  input that is not stored (for example digital-convert's layout of a mixed document) is named by
  its SHA-512 and marked as not stored;
- ``result``: the outputs, named by distribution and SHA-512; for the record, the blocks and
  fields the step wrote;
- ``agent``: who ran it (``Organization`` or ``Person``);
- ``startTime``, ``endTime`` and ``actionStatus``. What AMČR stores is always
  ``CompletedActionStatus``, because a failed job writes nothing; ``FailedActionStatus`` serves
  development and tests, which use the same frame;
- tool-specific data as properties of the action: only the parameters that shaped the output
  (model revision, thresholds, forced pages, the translator's field list), sampling and splitting
  notes, and each component with its version and terms, as facts, never combined into a licence.

The record has paradata of its own, ``paradata/atrium/document-json``: one action for each step
that wrote it. The ATRIUM services return their paradata in this shape; the orchestration adds the
job data. The profile pairs with the RO-Crate direction of ATRIUM, so paradata can become part of
an exported crate without conversion. Each paradata file describes the run that produced the
current version of its distribution; earlier runs are in the OCFL history.

Mappings, documented from the start:

.. list-table::
   :header-rows: 1
   :widths: 30 36 34

   * - Process Run Crate (schema.org)
     - W3C PROV-O
     - PREMIS 3
   * - ``CreateAction``
     - ``prov:Activity``
     - Event
   * - ``CreateAction`` type or ``additionalType``
     - type of the activity
     - ``eventType`` (capture, ingestion, migration, creation)
   * - ``instrument``
     - ``prov:wasAssociatedWith`` a ``prov:SoftwareAgent``
     - Agent (software), role "executing program"
   * - ``agent``
     - ``prov:wasAssociatedWith`` a ``prov:Person`` or ``prov:Organization``
     - Agent, role "implementer"
   * - ``object``
     - ``prov:used``
     - ``linkingObjectIdentifier``, role "source"
   * - ``result``
     - ``prov:generated``
     - ``linkingObjectIdentifier``, role "outcome"
   * - ``startTime``, ``endTime``
     - ``prov:startedAtTime``, ``prov:endedAtTime``
     - ``eventDateTime``
   * - ``actionStatus``
     - —
     - ``eventOutcomeInformation``
   * - tool-specific data
     - properties of the activity
     - ``eventDetailInformation``

*Considered and rejected:* a custom paradata format; the record as the only carrier of paradata;
serving paradata as plain ``application/json``; run data or block stamps inside the record.


Paradata of the original (``paradata/orig``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Agreed framework**, tracked in
`aiscr-webamcr#4315 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4315>`__.
``paradata/orig`` holds the history of the original as a list of events. Each event is written in
the transaction of the event it describes, so it adds no extra version.

- **Capture:** digitisation of a physical document, or creation of a born-digital one. It records
  the agent, date, device, software and settings, and the physical original where known.
- **Ingest:** upload, bulk import or migration, with the user or import batch, the date and the
  source system. Mass digitisation is recorded once per import batch.
- **Archival optimisation:** a PDF is converted to PDF/A-2b with Adobe Acrobat Preflight, using
  the published profile
  (`Formáty souborů <https://amcr-help.aiscr.cz/amcr/dokumenty.html#form%C3%A1ty-soubor%C5%AF>`__),
  and uploaded as a new version of the file through AMČR's file-update feature. That is possible
  only while the record is open for edits; archiving itself is a metadata operation and never
  changes the bytes of ``orig``. The event records the archivist, the software, the profile, and
  the SHA-512 of the old and the new bytes, and it is written in the transaction of that upload.
  Any new version replaces the bytes of ``orig``, so ``orig-format`` is regenerated in the same
  transaction.

It does not describe the technical format (``orig-format``), fixity (the Fedora digest), rights
(the record metadata), or the processing of derived files (their own paradata). A missing
``paradata/orig`` means "not recorded".

.. mermaid::
   :align: center

   flowchart LR
       C["capture<br/>digitisation or born-digital"] --> I["ingest<br/>upload, import or migration"]
       I --> O["archival optimisation<br/>new version, PDF/A-2b"]
       O -. "orig bytes change" .-> F["orig-format regenerated"]


Licences
--------

**Agreed.** No licence is computed anywhere: a component's licence is not the licence of an
output. Each output states its licence context in three layers.

.. list-table::
   :header-rows: 1
   :widths: 22 42 36

   * - Layer
     - What it says
     - Where the user finds it
   * - 1. Rights in the content
     - the document's own licence, otherwise AMČR's default CC BY-NC 4.0; derived distributions
       inherit it
     - the record crate (``license``), the File API (``Link rel="license"``), the Digital Archive,
       OAI and ARIADNE
   * - 2. Produced with
     - each step's components and their terms, listed, never merged into one licence
     - the distribution's paradata, shown beside the download
   * - 3. AMČR conditions
     - a condition of reuse AMČR decides to honour, stated with its reason
     - AMČR's policy, shown with layer 1

Outputs produced through LINDAT services (the linguistic layer, entities, ``atr/teitok-xml`` and
the machine-translated fields of ``metadata-en``) reach the production release only once their
terms are covered in writing
(`atrium-project#78 <https://github.com/ufal/atrium-project/issues/78>`__); the pilot proceeds
on ÚFAL's answer.

*Considered and rejected:* a licence calculated from the components and stored in the record or
the paradata, which asserts rights that no one decided.


The enrichment record (``atrium/document-json``)
------------------------------------------------

Schema and identity
~~~~~~~~~~~~~~~~~~~

**Agreed.** The record follows ``doc-schema-v2`` of the ATRIUM tools (record 2.0, released after
the pilot run on the cluster; ``doc-schema-v1`` stays as published). AMČR creates the first
version of each record itself, and it uses SHA-512 throughout.

- **Seeded by AMČR.** When a file is first processed, AMČR creates the baseline record and passes
  it to the first service:

  - ``doc_id`` = ``file_id``;
  - ``source.filename`` and ``source.media_type`` (from DROID);
  - ``source.sha512`` (the Fedora digest of ``orig``);
  - the required keys.

  The record builder in ocr-postprocess writes the rest of ``source``; ``source.origin`` only
  describes where the text came from.

  Every later stage inherits the baseline's ``doc_id``, so identity does not depend on filenames.
- **SHA-512 throughout.** The Fedora digest, the OCFL inventory, DROID's hash in ``orig-format``
  and ``source.sha512`` are one and the same value. Pairing them is a comparison with no extra
  hashing, and a mismatch stops processing for that file. ``source.sha512`` is an additive field,
  which the schema allows without a version change.
- **No run data.** The record carries no provenance, block stamps, references to tool-local
  files or calculated licence; each step that wrote it is described in
  ``paradata/atrium/document-json``.
- **Licence.** No licence is computed; see `Licences`_.
- The tool services are asked to accept an AMČR-seeded baseline on their first call, and to pass
  ``source.sha512`` through.

*Considered and rejected:* deriving ``doc_id`` from the uploaded filename, which ties identity to
naming; SHA-256 for the pairing, which AMČR does not use elsewhere.

What the record is
~~~~~~~~~~~~~~~~~~

**Agreed.** The record holds the content the tools derived for a document. It is not the
inventory of the file: which distributions exist is the ``DISTxx`` history. A stored distribution
that no tool reads does not need to appear in the record.

How the record is populated
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Agreed.** The record changes only through a processing run, and in the pilot every run goes
through the whole chain.

1. **An input arrives** (a new or replaced ``orig``, the converted mass OCR, the HPC ATR run): the
   layout level is produced or imported as ``atr/docproc-json``, and the record is built from it
   and enriched by the later steps.
2. **The schema or a tool changes:** the affected documents are run again, in the next planned
   bulk pass.
3. **A rerun changes nothing in a distribution:** a distribution whose SHA-512 is unchanged is
   kept, together with its paradata, which still describe it truthfully.

.. mermaid::
   :align: center

   flowchart LR
       IN["input arrives<br/>orig, converted mass OCR, HPC ATR run"] --> L["atr/docproc-json"]
       L --> B["record built<br/>(ocr-postprocess)"]
       B --> E["record enriched<br/>(later steps)"]
       E --> W["one transaction per record"]

*Considered and rejected:* a separate assembler service, which would duplicate tool logic and write
blocks that other tools own; a record-only mode for each tool (withdrawn on 13 October 2026), which
added a second way to change the record.

When processing runs
~~~~~~~~~~~~~~~~~~~~

**Agreed.** Processing runs on explicit invocation. An automatic trigger is optional.

- **Explicit invocation:** an admin page takes a CSV of identifiers (records or files) and the
  operation to run, and dispatches the jobs to the orchestration. It follows the existing admin operations on ``FedoraCustomAdminSite``
  (``update_doi``, ``update_metadata_file_upload``).
- **Optional automatic trigger,** switchable per task. When enabled, it fires on archiving, not on
  upload: only archived records are published, and the bytes of an archived record's ``orig`` do
  not change until the record is reopened for edits, because only a new version upload changes
  them and archiving itself is a metadata operation.
- **Staleness is detected:** a record whose ``source.sha512`` differs from the current digest of
  ``orig`` is out of date, and can be listed for the next invocation.

.. mermaid::
   :align: center

   sequenceDiagram
       actor A as Administrator
       participant W as AMČR
       participant O as Orchestration
       participant S as Tool services
       participant F as Fedora
       A->>W: invocation (CSV of identifiers, operation)
       W->>O: one job per file (seeded record, inputs)
       loop each stage
           O->>S: input and record
           S-->>O: output, record and paradata
       end
       O-->>W: results of the run
       W->>F: one transaction: distributions, paradata, record, history
       Note over F: one new OCFL version of the record


Record crate (RO-Crate)
-----------------------

**Agreed**, tracked in
`aiscr-webamcr#4316 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4316>`__. Every archived
record is an RO-Crate. AMČR stores ``ro-crate-metadata.json`` at the root of the record's
container, with ``@id`` values relative to the record. The same document is valid on disk and on
the web.

- **Version** (Confirmed): RO-Crate 1.2 with the Process Run Crate profile 0.5, the newest pair
  the RO-Crate validator supports, validated in two runs (the 1.2 base and the 0.5 profile). The
  crate and the paradata move to RO-Crate 1.3 with Process Run Crate 0.6 once the validator
  supports them; a version change rides along the next planned bulk pass rather than getting one of
  its own. Tests name the validator profile explicitly.
- **On disk:** Fedora keeps each binary at its record-relative path inside the record's OCFL
  object (``metadata``, ``file/{file_id}/orig``, ``file/{file_id}/atr/docproc-json``). OCFL stores the
  content under ``vN/content/`` per version, so the crate root is the object's head version as OCFL
  materialises it (for example an OCFL export), not the raw object directory. That state, with the
  metadata file at its root, is an *Attached* RO-Crate that can be read without Fedora or AMČR.
  Fedora's own files (``.fcrepo/``, ``~fcr-desc.nt``, ``fcr-container.nt``) are simply not
  described, which the specification allows.
- **On the web:** the File API mirrors the same paths, so the document served at
  ``/id/{ident_cely}/ro-crate`` (no extension, like the other PURLs) resolves its relative
  ``@id`` values to File API URLs. RO-Crate 1.2 resolves them against the final URL after
  redirects, so the crate is served without a redirect to another path, from the host whose
  ``/id/{ident_cely}/`` tree also serves the files. The name ``ro-crate-metadata.json`` is required
  only for the file on disk and for the descriptor's ``@id`` inside the JSON-LD.
- **Which records:** those that go through archiving: ``projekt``, ``archeologicky_zaznam``
  (events and sites), ``dokument`` (including the 3D library), ``samostatny_nalez``,
  ``ext_zdroj`` and ``pian``. Reference records (vocabulary terms, persons, organisations, users,
  RÚIAN) have no crate; they appear inside other crates as contextual entities.
- **When:** created at archiving, then maintained on every structural change of the archived
  record (a file or distribution added or removed, a rename) and on any change of a lifted field.
  It is generated deterministically and written only when it changed, in the transaction of the
  change that caused it. A bulk service on the admin pages creates or refreshes crates for
  archived records, after imports, and after changes of the generator.
- **No fixity:** the crate carries no digests. The OCFL inventory (a SHA-512 manifest) and
  ``premis:hasMessageDigest`` hold fixity; core RO-Crate 1.2 has no checksum property and leaves
  fixity to the packaging layer. Files carry ``contentSize``, which RO-Crate 1.2 recommends: a size
  changes only when the bytes change, which is a structural change that rewrites the crate anyway.
- **Restricted and absent files:** a file whose access is restricted is still present in the
  payload; Fedora holds it and only the File API's access rules deny it, so its relative ``@id``
  stays valid. A file that is really absent from a record is not described with a relative
  ``@id``.
- **Formats:** ``encodingFormat`` is the MIME type and the PRONOM URI from DROID
  (``orig-format``).
- **Paradata:** the ``CreateAction`` of each distribution's paradata is part of the crate's graph.
- **Root entity:** only the RO-Crate MUSTs and citation data, taken from public fields only (never
  from ``chranene_udaje``). The root ``@id`` is ``./``: RO-Crate 1.2 refuses an absolute root
  beside relative data entities. The Digital Archive URL
  (``https://digiarchiv.aiscr.cz/id/{ident_cely}``) is in ``url`` and ``identifier``;
  ``identifier`` and ``cite-as`` also carry the DOI or IGSN where one exists. ``name`` and
  ``creditText`` follow the Digital Archive's citations and
  BibTeX: ``Document {ident_cely}`` for documents, the title for external sources, and
  ``AMCR record {ident_cely}`` otherwise. ``datePublished`` is the archiving date for every type.
  ``license`` is the document's own licence (its SPDX URI), otherwise AMČR's default CC BY-NC 4.0.
- **Access:** the crate follows the record's access rules, as a child of ``/id/{ident_cely}/``.
- **Discovery:** the landing page links the crate through FAIR Signposting (``describedby``), and
  its schema.org JSON-LD matches the crate's root entity. ``/id/{ident_cely}/metadata`` and
  ``/id/{ident_cely}/metadata-en`` redirect to the OAI records, so relative ``@id`` values resolve
  on the web too
  (`aiscr-digiarchiv-2#140 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/140>`__).

.. mermaid::
   :align: center

   flowchart LR
       C["ro-crate-metadata.json<br/>at the record root"] --> D["on disk: the OCFL object<br/>is an Attached RO-Crate"]
       C --> W["on the web: /id/{ident_cely}/ro-crate<br/>relative @id resolve to the File API"]
       D --> X["fixity: OCFL inventory (SHA-512)"]
       W --> L["landing page links the crate<br/>(signposting describedby)"]

*Considered and rejected:* schema.org properties in Fedora's own RDF, which Fedora does not serve
as an RO-Crate document and which spread writes over many resources; a crate generated on demand,
which leaves the Fedora object not self-describing; the crate as the source of truth instead of
the ``DISTxx`` history, which would add a second write path; one crate per file.


Write plan
----------

**Agreed.**

1. **One transaction per record per run.** Between stages, the orchestration holds the
   intermediate record and outputs. At the end of a run, AMČR writes everything in one transaction:
   the distributions, their paradata, the record and its paradata, ``orig-format`` if it changed,
   the record crate if it changed, and the ``DISTxx`` history.
2. **One hand-over per job.** A run hands AMČR one list of results per file job: each distribution
   with its SHA-512, media type and paradata. A file job always carries the full set
   (``atr/docproc-json``, ``atrium/document-json``, ``atr/teitok-xml`` and their paradata).
   ``metadata-en`` is a record-level job of its own, run when the record is archived. The pipeline
   validates before handing over; AMČR validates and writes all of it in one transaction, or
   nothing. A failed job writes nothing
   (`aiscr-docs-pipeline#13 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/13>`__).
3. **Only changed resources are written.** An output identical to the stored one (same digest) is
   not rewritten.
4. **Few, planned bulk passes:**

   - the import of the existing mass OCR, converted once into ``atr/docproc-json``, with its
     paradata;
   - the full processing chain on the corpus, after a pilot and after the tool versions are pinned;
   - the ``metadata-en`` backfill over archived records;
   - the record-crate backfill over archived records.

   A tool change that alters results corpus-wide waits for the next planned pass.
5. **Large inputs** are split and merged by the orchestration. Stored distributions are always
   whole files.

*Considered and rejected:* storing the record after every stage, which multiplies the versions of
every record by the number of stages.


Open points
-----------

- **The normative layout schema**
  (`aiscr-docs-pipeline#17 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/17>`__): a
  required block identifier, tables, the links between blocks, and one vocabulary of block types
  and field names for both producers.
- **LINDAT terms in writing** before the production release
  (`atrium-project#78 <https://github.com/ufal/atrium-project/issues/78>`__).
- **The first stored pilot batch:** the converted mass OCR, or the ATR re-run where it has landed
  (`aiscr-webamcr#3529 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3529>`__).


Where each part is implemented
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Part
     - Home
   * - Paths, names, history, access
     - `aiscr-webamcr#3527 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3527>`__,
       `aiscr-digiarchiv-2#693 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/693>`__;
       user documentation in
       `aiscr-api-home#41 <https://github.com/ARUP-CAS/aiscr-api-home/pull/41>`__
   * - Distribution catalogue: producers
     - `aiscr-docs-pipeline#1 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/1>`__ and its stage issues,
       `aiscr-atr#1 <https://github.com/ARUP-CAS/aiscr-atr/issues/1>`__,
       `aiscr-atr#2 <https://github.com/ARUP-CAS/aiscr-atr/issues/2>`__,
       `aiscr-webamcr#3529 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3529>`__,
       `aiscr-webamcr#3583 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3583>`__,
       `aiscr-webamcr#4038 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4038>`__
   * - Distribution catalogue: consumers
     - `aiscr-digiarchiv-2#710 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/710>`__,
       `aiscr-digiarchiv-2#711 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/711>`__,
       `aiscr-digiarchiv-2#714 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/714>`__,
       `aiscr-digiarchiv-2#113 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/113>`__
   * - English metadata
     - `aiscr-webamcr#3570 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3570>`__ (generation),
       `aiscr-digiarchiv-2#496 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/496>`__
       (consumption)
   * - Paradata: AMČR side; record seeding, invocation, triggers and writes
     - `aiscr-webamcr#2590 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/2590>`__
   * - Paradata of the original
     - `aiscr-webamcr#4315 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4315>`__
   * - Record crate
     - `aiscr-webamcr#4316 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4316>`__
   * - Landing pages, signposting, crate serving and metadata redirects
     - `aiscr-digiarchiv-2#140 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/140>`__
   * - DROID pairing
     - `aiscr-webamcr#4038 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4038>`__
   * - Layout schema (``atr/docproc-json``)
     - `aiscr-docs-pipeline#17 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/17>`__
   * - Orchestration: route step, Temporal workflows, hand-over to AMČR
     - `aiscr-docs-pipeline#11 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/11>`__ to
       `aiscr-docs-pipeline#16 <https://github.com/ARUP-CAS/aiscr-docs-pipeline/issues/16>`__
   * - Record schema and the ATRIUM tools
     - `atrium-project#84 <https://github.com/ufal/atrium-project/issues/84>`__
       (``doc-schema-v2``)
   * - Published contract (selection)
     - `aiscr-api-home#29 <https://github.com/ARUP-CAS/aiscr-api-home/issues/29>`__ (File API
       page), and the AMČR help where fitting
