## Návrhy na zlepšení promptu pro T06 (Celery analýza)

- Doplnit explicitní poznámku, že v tomto projektu je beat schedule spravována přes `django_celery_beat` v databázi a z repozitáře ji nelze plně auditovat – agent by měl tuto skutečnost zaznamenat do `celery_analysis.json` místo pokusu rekonstruovat konkrétní plán.
- Přidat příklady typických Celery problémů s externími službami (HTTP volání bez timeoutu, chybějící retry politika) a doporučený způsob, jak je zapisovat do `error_handling_issues` / `timeout_issues` sekcí.
- Upřesnit, zda mají být do analýzy vždy zahrnuty i pomocné utility tasky (`write_value_to_redis`, jednoduché wrappery), nebo zda je stačí shrnout agregovaně pro daný modul a soustředit detailní popis jen na doménově důležité úlohy.

