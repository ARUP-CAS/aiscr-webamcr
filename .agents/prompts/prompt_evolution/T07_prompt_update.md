## Návrhy na zlepšení promptu pro T07 (frontend analýza)

- Výslovně uvést, že větší inline skripty v klíčových šablonách (např. `base.html`) mají být systematicky vyhledány, popsány a zařazeny do `template_inline_scripts.extraction_candidates` jako kandidáti na přesun do samostatných JS souborů.
- Do popisu T07 doplnit, že pokud projekt používá dark mode, má agent vždy samostatně zhodnotit způsob jeho implementace (využití `prefers-color-scheme`, datových atributů, SCSS vrstvy) a stručně jej shrnout ve `frontend_analysis.json`.
- Upřesnit vztah k CDN skriptům (např. Google Tag Manager, Analytics): očekává se, že agent stav SRI atributů pouze zdokumentuje, nikoliv automaticky vyhodnotí jako bezpečnostní chybu, pokud jde o first-party nástroje.

