## Návrhy na zlepšení promptu pro T08 (dokumentace)

- V sekci T08 přidat explicitní požadavek, aby agent posoudil i generátory využívající `subprocess` (např. licenční skripty) z hlediska error handlingu – kontrola `returncode`, práce s nevalidním výstupem a srozumitelnost chybových hlášek v CI.
- Doplnit, že u dokumentace testů (Selenium) má agent vždy ověřit, zda generátor test dokumentace vynucuje přítomnost klíčových sekcí (`Steps`, `Expected` apod.) a jak se chová v případě jejich absence; podle toho pak navrhnout zapojení do CI (např. selhání buildu).

