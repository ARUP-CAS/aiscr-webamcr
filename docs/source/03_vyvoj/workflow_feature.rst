Workflow požadavku
==================

Vizualizace toku práce nového požadavku (feature/enhancement) napříč etapami.

.. mermaid::
   :align: center

   flowchart TD

       A[Nový požadavek]

       B[#1 Working area]
       C[Předběžný návrh ARU]

       D[#2 Staging area]
       E[Odhad/analýza/omezení]

       F{Spadá do sprintu?}

       G[#3 Committed]
       H[#4 Maintenance & Claims]

       I[Test & deploy hotovo]

       J[#5 Acceptance]
       K[Neschváleno v akceptaci]

       %% Main flow
       A --> B
       B --> C
       C --> D
       D --> E
       E --> F

       %% Decision paths
       F -- ANO --> G
       F -- NE --> H

       %% Downstream flow
       G --> I
       H --> I

       I --> J
       J --> K

       %% Feedback / return loops
       K --> D

Workflow staging části
----------------------

Tok zpracování položek ve staging části backlogu.

.. mermaid::
   :align: center

   flowchart TD

       %% Entry points
       A1[Z boardu #5 Acceptance]
       A2[Z boardu #1 Working]

       %% Left branch (return from acceptance)
       B1[ARU test neprošel / bug]
       C1[K potvrzení]
       D1[DEV určí pipeline – vývoj/maintenance]
       E1[ARU schvaluje]

       %% Right branch (new request)
       B2[ARU: předběžný rozsah]
       C2{Je to jasné?}

       %% Decision handling
       D2[DEV – diskuze]
       E2[DEV – odhad]
       F2[Odhad hotov]
       G2[Připraveno k objednání]

       %% Outcomes
       H1[#3 Committed]
       H2[#4 Maintenance & Claims]

       %% Flows
       A1 --> B1
       B1 --> C1
       C1 --> D1
       D1 --> E1

       A2 --> B2
       B2 --> C2

       C2 -- NE --> D2
       C2 -- ANO --> E2

       D2 --> E2
       E2 --> F2
       F2 --> G2

       %% Final routing
       E1 --> H1
       E1 --> H2

       E2 --> H1
       E2 --> H2

Workflow implementace
---------------------

Tok implementace od příchodu ze staging boardu až po předání do acceptance.

.. mermaid::
   :align: center

   flowchart LR

       %% Entry
       A[Z boardu #2 Staging]
       B[Připraven k implementaci]

       %% Main flow
       A --> B

       %% Workflow columns
       B --> C[Backlog]
       C --> D[ToDo]
       D --> E[Doing]
       E --> F[Implemented]
       F --> G[Testing & Deployment]
       G --> H[Vývoj & testování dokončeno]
       H --> I[#5 Acceptance board]

       %% Descriptions under stages
       C --> C1[Prioritní požadavky vybrány]
       D --> D1[Přiřazen vývojář]
       E --> E1[Připraveno na rebase na dev]
       F --> F1[V DEV testování / nasazeno]
