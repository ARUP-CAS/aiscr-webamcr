# Návrhy na zlepšení promptu — T05 (Security Analysis)

**Datum:** 2026-03-08
**Agent:** Claude (claude-sonnet-4-6)

---

## Co v promptu chybělo nebo bylo nejasné

### 1. Checklist pro `manage.py check --deploy`

Prompt nezmiňuje Django's vestavěný deployment checklist (`python manage.py check --deploy`). Tento nástroj je prvním krokem bezpečnostního auditu Django aplikací — automaticky zkontroluje všechny bezpečnostní nastavení a vypíše varování. Měl by být součástí T05 jako první krok.

**Návrh přidat do sekce T05:**
```
- Spustit `python manage.py check --deploy` a zaznamenat výstupy
  (DEBUG, SECRET_KEY, ALLOWED_HOSTS, HTTPS settings, cookie security)
```

### 2. Instrukce pro CVE scanning

Prompt zmiňuje "dependencies with known CVEs" ale neposkytuje konkrétní metodu. V offline prostředí (bez přístupu k pip index nebo safety.io) je to neproveditelné. Měl by být navržen fallback:

**Návrh přidat:**
```
CVE scanning:
- Primárně: spustit `pip audit` nebo `safety check` v CI pipeline
- Pokud nástroje nejsou dostupné: zaznamenat jako "CVE audit doporučen"
  a přidat do refactoring_backlog jako SEC krok
```

### 3. Scope pro mark_safe() audit

Prompt zmiňuje "XSS risks (`safe` filters in templates, `mark_safe()`)" ale neuvádí jak rozlišit akceptovatelné (hardcoded HTML widgets) od problematických (DB hodnoty). Jasné kritérium by pomohlo:

**Návrh přidat:**
```
mark_safe() hodnocení:
- Přijatelné: hardcoded HTML string bez uživatelského vstupu (widget dekorace)
- Střední risk: hodnota z model property nebo DB atributu bez explicitního escape()
- Vysoké risk: hodnota přímo z request parametrů nebo uživatelského vstupu
Preferovaný vzor: format_html() místo mark_safe() pro dynamický obsah
```

### 4. Audit pattern pro secrets v commitu

Prompt pokrývá "sensitive files in .gitignore vs committed" ale chybí konkrétní instrukce jak rozlišit placeholder od reálných credentials:

**Návrh přidat:**
```
Při auditu sample secrets souborů:
- Placeholder znaky: "changeme", "test_key", "PLACEHOLDER", "your_key_here", "secret"
- Potenciálně reálné: náhodně vypadající hex/base64 řetězce, email adresy,
  URL s doménou třetí strany
- Pokud credentials vypadají jako reálné, zaznamenat jako Střední závažnost
  a doporučit rotaci
```

### 5. Instrukce pro AMCRAuthUser pattern

Prompt nezmiňuje audit authentication backendu. Nestandardní implementace `user_can_authenticate()` (výjimka místo False) je bezpečnostně relevantní pattern, který by měl být explicitně hledán.

**Návrh přidat do T05 sekce Authentication:**
```
- Ověřit `user_can_authenticate()` v custom backend: musí vracet False (ne výjimku) pro neaktivní uživatele
```

---

## Co by příštímu agentovi pomohlo

1. **Přístup k GitHub Issues** pro cross-reference — bez autentizace jsou issues nedostupné; agent by mohl zkusit `gh issue list` CLI pokud je GitHub CLI dostupné.

2. **Přehled NGINX konfigurace** (`proxy/default.conf`) by měl být součástí T05 scope, protože HTTPS hlavičky mohou být na proxy vrstvě, ne v Django settings.

3. **Znát framework verzi** — Django 5.2 (z AGENTS.md) má specifické security defaults; je užitečné citovat Django dokumentaci pro danou verzi.

---

## Jaké soubory nebo adresáře by stálo za to přidat do T05 scope

- `proxy/default.conf` — ověření HSTS, SSL redirect a security hlaviček na NGINX vrstvě (kritické pro pochopení SEC-03)
- `webclient/core/middleware.py` nebo `webclient/core/middleware/` — custom middleware může ovlivnit bezpečnost
- `webclient/webclient/urls.py` — debug views, admin URL path (potencionálně předvídatelný)
- Všechny soubory přiřazené `get_ident_cely_link` property (modely s tímto atributem) pro ověření XSS-02
