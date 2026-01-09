Workflow implementace požadavku
==================

Vizualizace implementace nového požadavku (feature/enhancement) napříč etapami.

.. mermaid::
   :align: center

   flowchart TD

       A[Požadavek/Hlášení chyby]
       B1[Design]
       B2[Duscussion]
       B3[Estimate]
       B4[Backlog]
       C1[To do]
       C2[In progress]
       C3[Review]
       C4[Deployment]
       D1[Testing blocked]
       D2[Testing ready]
       D3[Testing in progress]
       D4[Accepted]
       E[Released to production]
       Z[Uzavřeno]

       A -- vytvoření issue --> B1
       subgraph Working
           direction LR
           B1 <-- upřesnění --> B2 
           B1 -- odhad náročnosti --> B3 -- zařazení do zásobníku --> B4
         end
       B4 -- zařazení do vývoje --> C1
       subgraph Development
           direction LR
           C1 -- zahájení vývoje --> C2 -- vytvoření pull request --> C3 -- nezávislé potvrzení revizory --> C4
         end
       C4 -. čeká na splnění jiných podmínek .-> D1
       C4 -- nový release nasazen na test prostředí --> D2       
       subgraph Acceptance
           direction LR
           D1 -. podmínky pro testování splněny .-> D2 -- testování zahájeno --> D3 -- potvrzení funkčnosti --> D4
         end
       D3 -. nalezena chyba, návrat do vývoje .-> C1 
       D4 -- uzavření issue a nasazení do produkce --> E
       E -- vypořádání se zadavatelem --> Z

