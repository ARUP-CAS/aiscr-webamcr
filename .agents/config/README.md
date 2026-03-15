# .agents/config

Konfigurační soubory a perzistentní stav pro dlouhodobý technický review.

## Soubory

- `review_config.yaml`  
  - definice tasků (T01–T11), jejich priority a rozsahu,
  - technický stack, adresáře v rozsahu, vendored výjimky,
  - limity velikosti tasků (počty řádků/souborů).

- `review_cache.json`  
  - stav jednotlivých tasků (`pending`, `done`, `split`, `blocked`…),
  - poslední čas aktualizace,
  - hash souborů a informace o tom, kterým taskem byly naposledy revidovány.

## Poznámky

- `review_config.yaml` je kanonickým zdrojem konfigurace — hodnoty z něj **neopisovat**
  do promptů ani jiných souborů, ale pouze odkazovat.
- `review_cache.json` se přepisuje automaticky agenty; ruční úpravy pouze ve výjimečných
  případech a po dohodě týmu.

