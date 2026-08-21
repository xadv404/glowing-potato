#!/usr/bin/env python3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# {q} = keyword (quoted if multi-word by build_dork).
# Google : inurl:.php?id= mort depuis ~2023 (query strings non indexées).
#           → strings d'erreur en guillemets + ext: operator.
# Bing   : inurl: fonctionne encore sur les query strings.
#           → inbody: à la place de intext:.

# ── Templates Google (2026) ───────────────────────────────────────────────────
# intext: force la recherche dans le corps de la page uniquement
# (sans intext: Google matche aussi titres/meta/anchors → faux positifs)
SQLI_GOOGLE_TEMPLATES = [
    # MySQL / MySQLi
    'intext:"You have an error in your SQL syntax" {q}',
    'intext:"You have an error in your SQL syntax near" {q}',
    'intext:"mysql_fetch_array() expects parameter 1 to be resource" {q}',
    'intext:"mysql_num_rows() expects parameter 1 to be resource" {q}',
    'intext:"mysql_fetch_assoc() expects parameter 1 to be resource" {q}',
    'intext:"supplied argument is not a valid MySQL result resource" {q}',
    'intext:"Warning: mysql_query()" {q}',
    'intext:"Warning: mysql_connect()" {q}',
    'intext:"MySQL Error: 1064" {q}',
    'intext:"Warning: mysqli_fetch_array()" {q}',
    'intext:"Warning: mysqli_num_rows()" {q}',
    'intext:"mysqli_fetch_array() expects parameter 1 to be mysqli_result" {q}',
    'intext:"Error Executing Database Query" {q}',
    'intext:"mySQL error with query" {q}',
    # PDO
    'intext:"PDOException: SQLSTATE" {q}',
    'intext:"SQLSTATE[42000]: Syntax error or access violation" {q}',
    'intext:"SQLSTATE[HY000]" {q}',
    'intext:"PDO::query(): SQLSTATE" {q}',
    # PostgreSQL
    'intext:"pg_query(): Query failed:" {q}',
    'intext:"pg_exec(): Query failed:" {q}',
    'intext:"Warning: pg_connect()" {q}',
    'intext:"unterminated quoted string at or near" {q}',
    'intext:"ERROR: syntax error at or near" {q}',
    'intext:"Supplied argument is not a valid PostgreSQL result" {q}',
    'intext:"PostgreSQL query failed: ERROR: parser: parse error" {q}',
    # MSSQL / SQL Server
    'intext:"Microsoft OLE DB Provider for SQL Server" {q}',
    'intext:"Unclosed quotation mark after the character string" {q}',
    'intext:"Unclosed quotation mark before the character string" {q}',
    'intext:"[Microsoft][ODBC SQL Server Driver]" {q}',
    'intext:"[Microsoft][SQL Native Client][SQL Server]" {q}',
    'intext:"[SQL Server Driver][SQL Server]Line 1: Incorrect syntax near" {q}',
    'intext:"Incorrect syntax near" {q}',
    'intext:"Warning: mssql_query()" {q}',
    'intext:"80040e14" intext:"Microsoft OLE DB" {q}',
    # Oracle
    'intext:"ORA-00933: SQL command not properly ended" {q}',
    'intext:"ORA-00907: missing right parenthesis" {q}',
    'intext:"ORA-01756: quoted string not properly terminated" {q}',
    'intext:"ORA-00921: unexpected end of SQL command" {q}',
    'intext:"ORA-00936: missing expression" {q}',
    'intext:"Warning: oci_connect()" {q}',
    # SQLite
    'intext:"SQLite3::query(): Unable to prepare statement" {q}',
    'intext:"SQLiteException: no such table" {q}',
    'intext:"Warning: SQLite3::exec()" {q}',
]

SQLI_TEMPLATES = SQLI_GOOGLE_TEMPLATES  # compat
ALL_TEMPLATES = SQLI_GOOGLE_TEMPLATES

SQLI_HQ_TEMPLATES = SQLI_GOOGLE_TEMPLATES
SQLI_SQL_TEMPLATES = SQLI_GOOGLE_TEMPLATES


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

    print(f"{len(keywords)} keywords × {len(tpl)} templates SQLi = {len(dorks)} dorks")
    if domain:
        print(f"Domaine : {domain}")
    print(f"Sauvegardé : {output_path}")

    return len(dorks), output_path


if __name__ == "__main__":
    from gui import main as gui_main

    gui_main()
