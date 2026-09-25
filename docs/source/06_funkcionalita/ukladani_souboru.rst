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
       F --> AT["atr/alto-xml · atr/lines-csv · atr/teitok-xml"]
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
     - ``image/png``, ``image/jpeg``
     - AMČR (Implemented)
     - `aiscr-webamcr#3527 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3527>`__
   * - ``orig-format``
     - ``text/csv``
     - AMČR: DROID's own CSV export for the file, hash set to SHA-512
     - `aiscr-webamcr#4038 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/4038>`__
   * - ``atrium/document-json``
     - ``application/json``
     - every processing run
     - `aiscr-webamcr#2590 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/2590>`__
   * - ``atr/alto-xml``
     - ``application/xml``
     - ATR service, or the existing mass-OCR ALTO
     - `aiscr-webamcr#3529 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3529>`__
   * - ``atr/lines-csv``
     - ``text/csv``
     - alto-postprocess (per-line quality table)
     - `aiscr-webamcr#3530 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3530>`__,
       `aiscr-digiarchiv-2#714 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/714>`__
   * - ``atr/teitok-xml``
     - ``application/xml``
     - nlp-enrich
     - `aiscr-webamcr#3531 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3531>`__,
       `aiscr-digiarchiv-2#711 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/711>`__,
       `aiscr-digiarchiv-2#113 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/113>`__
   * - ``cva/coco-json``
     - ``application/json``
     - vision-detect (ARÚB; family kept open)
     - `aiscr-webamcr#3583 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3583>`__
   * - ``cva/wadm``
     - ``application/ld+json``
     - AMČR, converted from ``cva/coco-json`` (family kept open)
     - `aiscr-webamcr#3583 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3583>`__

Kept only in the record, with no file of their own:

- **page classification** (``page_categories``, ``pages[].category*``). Its results are already
  persisted in the record, and the Digital Archive reads them from there
  (`aiscr-digiarchiv-2#710 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/710>`__);
- **keywords**, in two kinds labelled by kind: *controlled* keywords from the vocabulary step of
  llm-enrich (its ``enrichment`` block, with concept identifiers), and *uncontrolled* statistical
  keywords from nlp-enrich, with method and score (a ``keywords`` block, requested from the tool
  maintainers). The default method is KeyBERT; YAKE and the legacy KER method stay selectable. Consumers decide how to use them: free keywords, schema.org ``keywords``, an
  evaluation baseline, candidates for new vocabulary terms;
- **born-digital text lines**, whose persistent source is the original itself.

The ``atrium/`` family is reserved for the record, and ``atrium/document-json`` is its final name.
It matches the tools' ``.document.json`` files and the ``atrium_document`` schema.

*Considered and rejected:* a ``cva/pages-csv`` file for page classification, which duplicates the
record; converting the DROID output into another format, which would add a conversion to
maintain. The name ``atr/stats-csv``, used only on a temporary test fixture, is replaced by
``atr/lines-csv``.


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
  the translator
  (`aiscr-webamcr#3570 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3570>`__), selected by
  its XPath definitions and translated in place.
- **Generated** asynchronously after archiving, in its own transaction. That adds one version per
  archiving event. Existing archived records get it in one planned bulk pass.
- **Stored** at ``rest/AMCR/record/{ident_cely}/metadata-en`` (``application/xml``), a sibling of
  ``metadata``. Its paradata is at ``rest/AMCR/record/{ident_cely}/paradata/metadata-en`` and
  records, among other things, the SHA-512 of the ``metadata`` it was built from.
- **History:** ``DIST01``/``DIST11`` with the note ``metadata-en``, in the record's history.
- **Licence:** the licence of the machine translation is stated in its paradata and shown with the
  English metadata.
- **Consumed** by
  `aiscr-digiarchiv-2#496 <https://github.com/ARUP-CAS/aiscr-digiarchiv-2/issues/496>`__.

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

- ``instrument``: the ``SoftwareApplication`` with its ``softwareVersion``, and for services the
  ``ContainerImage`` with its digest;
- ``object``: the inputs, named by distribution;
- ``result``: the output distribution;
- ``agent``: who ran it (``Organization`` or ``Person``);
- ``startTime``, ``endTime`` and ``actionStatus`` (``CompletedActionStatus`` or
  ``FailedActionStatus``);
- tool-specific data (the ATRIUM paradata: configuration, statistics, licence derivation) as
  properties of the action.

The tool services are asked to return their paradata in this shape. Until they do, the
orchestration composes it from the service response and the job metadata. The profile pairs with
the RO-Crate direction of ATRIUM, so paradata can become part of an exported crate without
conversion.

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
serving paradata as plain ``application/json``.


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
- **Archival optimisation:** at archiving, PDFs are converted to PDF/A-2b with Adobe Acrobat
  Preflight, using the published profile
  (`Formáty souborů <https://amcr-help.aiscr.cz/amcr/dokumenty.html#form%C3%A1ty-soubor%C5%AF>`__).
  The event records the archivist, the software, the profile, and the SHA-512 of the old and the
  new bytes. It replaces the bytes of ``orig``, so ``orig-format`` is regenerated in the same
  transaction.

It does not describe the technical format (``orig-format``), fixity (the Fedora digest), rights
(the record metadata), or the processing of derived files (their own paradata). A missing
``paradata/orig`` means "not recorded".

.. mermaid::
   :align: center

   flowchart LR
       C["capture<br/>digitisation or born-digital"] --> I["ingest<br/>upload, import or migration"]
       I --> O["archival optimisation<br/>PDF/A-2b"]
       O -. "orig bytes change" .-> F["orig-format regenerated"]


The enrichment record (``atrium/document-json``)
------------------------------------------------

Schema and identity
~~~~~~~~~~~~~~~~~~~

**Agreed.** The record follows the ``atrium_document`` schema 1.0 of the ATRIUM tools. AMČR
creates the first version of each record itself, and it uses SHA-512 throughout.

- **Seeded by AMČR.** When a file is first processed, AMČR creates the baseline record and passes
  it to the first service:

  - ``doc_id`` = ``file_id``;
  - ``source.filename`` and ``source.media_type`` (from DROID);
  - ``source.sha512`` (the Fedora digest of ``orig``);
  - the required keys.

  Every later stage inherits the baseline's ``doc_id``, and the first writer of each ``source``
  field wins. So identity does not depend on filenames.
- **SHA-512 throughout.** The Fedora digest, the OCFL inventory, DROID's hash in ``orig-format``
  and ``source.sha512`` are one and the same value. Pairing them is a comparison with no extra
  hashing, and a mismatch stops processing for that file. ``source.sha512`` is an additive field,
  which the schema allows without a version change.
- **References.** ``derived_from`` names stored outputs by their distribution name (for example
  ``"teitok": "atr/teitok-xml"``); ``regenerable`` holds recipes only.
- **Licence.** The record's accumulated licence (``provenance.license``) is shown with the record
  and its enrichments.
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

**Agreed.** The record changes only through processing and through each tool's record-only mode.

1. **An input arrives** (a new or replaced ``orig``, an imported ALTO, a curator's corrected ALTO,
   any future input): the stages that consume it can run, and they update the record.
2. **An output arrives without its tool running** (an imported TEITOK, COCO, or any future
   distribution a tool would produce): the owning tool runs in a *record-only mode*. It reads its
   own stored output and returns only its record block, with no compute. Block ownership stays
   with the tool.
3. **The schema or a tool's record hook changes:** the affected tools run in record-only mode over
   the stored outputs.

Imports cannot be predicted, so the mechanism stays generic: any distribution with an owning tool
can be reflected in the record. The record-only mode is requested from the tool maintainers.

.. mermaid::
   :align: center

   flowchart LR
       IN["input arrives<br/>orig, imported or corrected ALTO"] --> ST["consuming stages run"]
       OUT["output arrives without its tool<br/>imported TEITOK, COCO"] --> RO["owning tool in record-only mode"]
       MIG["schema or record hook changes"] --> RO
       ST --> R["record updated"]
       RO --> R
       R --> W["one transaction per record"]

*Considered and rejected:* a separate assembler service, which would duplicate tool logic and write
blocks that other tools own.

When processing runs
~~~~~~~~~~~~~~~~~~~~

**Agreed.** Processing runs on explicit invocation. An automatic trigger is optional.

- **Explicit invocation:** an admin page takes a CSV of identifiers (records or files) and the
  operation (the stages to run, or a record-only rebuild), and dispatches the jobs to the
  orchestration. It follows the existing admin operations on ``FedoraCustomAdminSite``
  (``update_doi``, ``update_metadata_file_upload``).
- **Optional automatic trigger,** switchable per task. When enabled, it fires on archiving, not on
  upload: archiving can replace the bytes of ``orig`` (the PDF/A optimisation), and only archived
  records are published.
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

- **On disk:** Fedora keeps each binary at its record-relative path inside the record's OCFL
  object (``metadata``, ``file/{file_id}/orig``, ``file/{file_id}/atr/alto-xml``). With the
  metadata file at the root, the OCFL object is an *Attached* RO-Crate 1.2 that can be read without
  Fedora or AMČR. Fedora's own files (``.fcrepo/``, ``~fcr-desc.nt``, ``fcr-container.nt``) are
  simply not described, which the specification allows.
- **On the web:** the File API mirrors the same paths, so the document served at
  ``/id/{ident_cely}/ro-crate`` (no extension, like the other PURLs) resolves its relative
  ``@id`` values to File API URLs. The name ``ro-crate-metadata.json`` is required only for the
  file on disk and for the descriptor's ``@id`` inside the JSON-LD.
- **Which records:** those that go through archiving: ``projekt``, ``archeologicky_zaznam``
  (events and sites), ``dokument`` (including the 3D library), ``samostatny_nalez``,
  ``ext_zdroj`` and ``pian``. Reference records (vocabulary terms, persons, organisations, users,
  RÚIAN) have no crate; they appear inside other crates as contextual entities.
- **When:** created at archiving, then maintained on every structural change of the archived
  record (a file or distribution added or removed, a rename) and on any change of a lifted field.
  It is generated deterministically and written only when it changed, in the transaction of the
  change that caused it. A bulk service on the admin pages creates or refreshes crates for
  archived records, after imports, and after changes of the generator.
- **No fixity:** the crate carries no digests or sizes. The OCFL inventory (a SHA-512 manifest)
  and ``premis:hasMessageDigest`` hold fixity; core RO-Crate 1.2 has no checksum property and
  leaves fixity to the packaging layer.
- **Formats:** ``encodingFormat`` is the MIME type and the PRONOM URI from DROID
  (``orig-format``).
- **Paradata:** the ``CreateAction`` of each distribution's paradata is part of the crate's graph.
- **Root entity:** only the RO-Crate MUSTs and citation data, taken from public fields only (never
  from ``chranene_udaje``). The root ``@id`` is the Digital Archive URL
  (``https://digiarchiv.aiscr.cz/id/{ident_cely}``); ``identifier`` and ``cite-as`` carry the DOI
  or IGSN where one exists. ``name`` and ``creditText`` follow the Digital Archive's citations and
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
2. **Only changed resources are written.** An output identical to the stored one (same digest) is
   not rewritten.
3. **Few, planned bulk passes:**

   - the import of the existing mass-OCR ALTO with its paradata;
   - the full processing chain on the corpus, after a pilot and after the tool versions are pinned;
   - the ``metadata-en`` backfill over archived records;
   - the record-crate backfill over archived records.

   A tool change that alters results corpus-wide waits for the next planned pass.
4. **Large inputs** are split and merged by the orchestration. Stored distributions are always
   whole files.

*Considered and rejected:* storing the record after every stage, which multiplies the versions of
every record by the number of stages.


Open points
-----------

- **Requests to the ATRIUM tool maintainers:** accept a seeded baseline and pass
  ``source.sha512`` through; return paradata as a Process Run Crate ``CreateAction``; provide a
  record-only mode; align ``atrium_rocrate.py`` with the record crate (RO-Crate 1.2, stable run and
  tool identifiers, tool authors on each ``SoftwareApplication``, an embeddable fragment); a
  ``keywords`` block for the uncontrolled keywords of nlp-enrich.


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
     - `aiscr-webamcr#3528 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3528>`__,
       `aiscr-webamcr#3529 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3529>`__,
       `aiscr-webamcr#3530 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3530>`__,
       `aiscr-webamcr#3531 <https://github.com/ARUP-CAS/aiscr-webamcr/issues/3531>`__,
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
   * - Requests to the ATRIUM tools
     - `ufal/atrium-project <https://github.com/ufal/atrium-project>`__ (issues to follow)
   * - Published contract (selection)
     - `aiscr-api-home#29 <https://github.com/ARUP-CAS/aiscr-api-home/issues/29>`__ (File API
       page), and the AMČR help where fitting
