## Návrhy na zlepšení promptu pro T09 (CI/CD analýza)

- V zadání T09 výslovně uvést, že agent má zhodnotit nejen přítomnost testovacích workflow a pre-commit hooků, ale i existenci bezpečnostních skenů na úrovni kontejnerů (Docker Scout, Trivy) a statické analýzy kódu (CodeQL, Bandit, apod.).
- Doplnit požadavek, aby agent ověřil, zda je nakonfigurován Dependabot (soubor `.github/dependabot.yml`) pro Python závislosti a GitHub Actions, a v případě absence navrhl vhodnou konfiguraci.
- Upřesnit, že do `cicd_analysis.json` se mají zaznamenat nejen technické parametry workflow (triggery, time-outy), ale i shrnutí, jak CI/CD pipeline podporuje bezpečnost (podpis image, SBOM, SARIF, provenance).

