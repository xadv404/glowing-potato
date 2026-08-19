#!/usr/bin/env python3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# {q} = keyword (quoted if multi-word by build_dork).
# Sources: GHDB 2026, SecOps, NVD CVE advisories, WPScan.

SQLI_TEMPLATES = [
    # ── MySQL / MySQLi erreurs confirmées ─────────────────────────────────
    'inurl:.php?id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?id= intext:"mysql_fetch_array() expects parameter 1" {q}',
    'inurl:.php?id= intext:"mysql_num_rows() expects parameter 1" {q}',
    'inurl:.php?id= intext:"mysql_fetch_assoc() expects parameter 1" {q}',
    'inurl:.php?id= intext:"supplied argument is not a valid MySQL" {q}',
    'inurl:.php?id= intext:"Warning: mysql_query()" {q}',
    'inurl:.php?id= intext:"MySQL Error: 1064" {q}',
    'inurl:.php?id= intext:"mysql_result(): supplied argument" {q}',
    'inurl:.php?catid= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?cat= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?pid= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?item= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?page= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?news_id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?article_id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?product_id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?cid= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?sid= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?tid= intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?uid= intext:"You have an error in your SQL syntax" {q}',
    'intext:"Warning: mysqli_fetch_array()" {q}',
    'intext:"Warning: mysqli_num_rows()" {q}',
    'intext:"Warning: mysqli_fetch_assoc()" {q}',
    'intext:"mysqli_fetch_array() expects parameter 1 to be mysqli_result" {q}',
    'intext:"mysql_num_rows()" intext:"mysql_fetch_array()" intext:"mysql_query()" {q}',
    'intext:"Error Executing Database Query." intext:"SQL" {q}',
    # ── PDO erreurs confirmées ─────────────────────────────────────────────
    'inurl:.php?id= intext:"SQLSTATE[42000]: Syntax error" {q}',
    'intext:"PDOException: SQLSTATE" {q}',
    'intext:"PDO::query(): SQLSTATE" {q}',
    'intext:"SQLSTATE[HY000]" intext:"query" {q}',
    # ── PostgreSQL erreurs confirmées ──────────────────────────────────────
    'inurl:.php?id= intext:"PostgreSQL query failed: ERROR" {q}',
    'intext:"pg_query(): Query failed:" {q}',
    'intext:"pg_exec(): Query failed:" {q}',
    'inurl:id= intext:"unterminated quoted string at or near" {q}',
    'intext:"ERROR: syntax error at or near" {q}',
    # ── MSSQL / SQL Server erreurs confirmées ──────────────────────────────
    'inurl:id= intext:"Microsoft OLE DB Provider for SQL Server" {q}',
    'inurl:id= intext:"Unclosed quotation mark after the character string" {q}',
    'intext:"[Microsoft][ODBC SQL Server Driver]" {q}',
    'intext:"[Microsoft][SQL Native Client][SQL Server]" {q}',
    'intext:"Incorrect syntax near" intext:"SQL" {q}',
    'intext:"Warning: mssql_query()" {q}',
    'inurl:.asp?id= intext:"Syntax error" intext:"query" {q}',
    'inurl:.aspx?id= intext:"SqlException" {q}',
    # ── Oracle erreurs confirmées ──────────────────────────────────────────
    'inurl:id= intext:"ORA-01756: quoted string not properly terminated" {q}',
    'inurl:.php?id= intext:"ORA-00921: unexpected end of SQL command" {q}',
    'intext:"ORA-00933: SQL command not properly ended" {q}',
    'intext:"ORA-00907: missing right parenthesis" {q}',
    'intext:"ORA-00936: missing expression" {q}',
    # ── SQLite erreurs confirmées ──────────────────────────────────────────
    'intext:"SQLite3::query(): Unable to prepare statement" {q}',
    'intext:"Warning: SQLite3::exec()" intext:"syntax error" {q}',
    'intext:"SQLiteException: no such table" {q}',
]

ALL_TEMPLATES = SQLI_TEMPLATES

# Aliases
SQLI_HQ_TEMPLATES = SQLI_TEMPLATES
SQLI_SQL_TEMPLATES = SQLI_TEMPLATES


def quote_keyword(keyword: str) -> str:
    keyword = keyword.strip()
    if " " in keyword:
        return f'"{keyword}"'
    return keyword


def load_lines(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    lines = []
    seen = set()

    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip().lower()
        if not value or value.startswith("#") or value in seen:
            continue
        seen.add(value)
        lines.append(value)

    if not lines:
        raise ValueError(f"Aucun keyword trouvé dans {path}")

    return lines


def build_dork(keyword: str, template: str, domain: str | None = None) -> str:
    q = quote_keyword(keyword)
    dork = template.format(q=q)
    if domain:
        return f"site:{domain} {dork}"
    return dork


def generate_dorks(
    keywords: list[str],
    domain: str | None = None,
    templates: list[str] | None = None,
) -> list[str]:
    tpl = templates if templates is not None else ALL_TEMPLATES
    dorks: list[str] = []
    for keyword in keywords:
        for template in tpl:
            dorks.append(build_dork(keyword, template, domain))
    return dorks


def _check_one(dork: str, delay: float) -> tuple[str, bool]:
    """Vérifie via DuckDuckGo HTML si un dork retourne au moins un résultat."""
    time.sleep(delay)
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, params={"q": dork}, headers=headers, timeout=12)
        has_results = 'class="result__a"' in resp.text or 'class="results_links"' in resp.text
        return dork, has_results
    except Exception:
        return dork, True  # erreur réseau → on garde


def validate_dorks(
    dorks: list[str],
    max_workers: int = 4,
    delay: float = 1.0,
) -> list[str]:
    """
    Filtre les dorks en vérifiant que DuckDuckGo retourne ≥ 1 résultat.
    Utile pour éliminer les templates qui ne matchent rien.
    Retourne les dorks valides (avec résultats).
    """
    valid: list[str] = []
    args = [(d, delay * i / max_workers) for i, d in enumerate(dorks)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_check_one, d, offset): d for d, offset in args}
        for future in as_completed(futures):
            dork, has_results = future.result()
            if has_results:
                valid.append(dork)

    return valid


def validate_templates(
    sample_keyword: str,
    templates: list[str] | None = None,
    max_workers: int = 5,
    delay: float = 0.8,
) -> list[str]:
    """
    Vérifie chaque template avec un keyword de référence.
    Retourne les templates qui donnent ≥ 1 résultat sur DuckDuckGo.
    Utile pour élaguer les templates morts avant la génération en masse.
    """
    tpl = templates if templates is not None else ALL_TEMPLATES
    test_dorks = [build_dork(sample_keyword, t) for t in tpl]
    valid_dorks = set(validate_dorks(test_dorks, max_workers=max_workers, delay=delay))
    return [t for t, d in zip(tpl, test_dorks) if d in valid_dorks]


def save_dorks(dorks: list[str], output_path: Path) -> None:
    output_path.write_text("\n".join(dorks) + "\n", encoding="utf-8")


def run_generator(
    input_path: Path,
    output_path: Path | None = None,
    domain: str | None = None,
    templates: list[str] | None = None,
    validate: bool = False,
) -> tuple[int, Path]:
    if output_path is None:
        stem = input_path.stem.removesuffix("_keywords")
        output_path = input_path.with_name(f"{stem}_dorks.txt")

    tpl = templates if templates is not None else ALL_TEMPLATES
    keywords = load_lines(input_path)
    dorks = generate_dorks(keywords, domain=domain, templates=tpl)

    if validate:
        print(f"Validation DuckDuckGo : {len(dorks)} dorks en cours…")
        dorks = validate_dorks(dorks)
        print(f"Dorks valides : {len(dorks)}")

    save_dorks(dorks, output_path)

    tpl_counts = {
        "SQLi": len(SQLI_TEMPLATES),
        "LFI": len(LFI_TEMPLATES),
        "Admin": len(ADMIN_TEMPLATES),
        "Sensitive": len(SENSITIVE_TEMPLATES),
    }
    tpl_summary = " + ".join(f"{v} {k}" for k, v in tpl_counts.items())
    print(
        f"{len(keywords)} keywords × {len(tpl)} templates ({tpl_summary})"
        f" = {len(dorks)} dorks"
    )
    if domain:
        print(f"Domaine : {domain}")
    print(f"Sauvegardé : {output_path}")

    return len(dorks), output_path


if __name__ == "__main__":
    from gui import main as gui_main

    gui_main()
