#!/usr/bin/env python3
from pathlib import Path

# UHQ SQLi dork templates — param + error combos, CMS-specific, CVE 2024-2025, SQL dumps.
# Only templates with confirmed-error or known-vulnerable-endpoint signal.
# {q} = keyword (quoted if multi-word by build_dork).
# Sources: GHDB 2026, SecOps, NVD CVE advisories, WPScan, Box Piper 2026.

SQLI_TEMPLATES = [
    # ── Tier 1 : MySQL / MySQLi erreurs confirmées ────────────────────────
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
    'intext:"Warning: mysqli_fetch_array()" {q}',
    'intext:"Warning: mysqli_num_rows()" {q}',
    'intext:"Warning: mysqli_fetch_assoc()" {q}',
    'intext:"mysqli_fetch_array() expects parameter 1 to be mysqli_result" {q}',
    'intext:"mysql_num_rows()" intext:"mysql_fetch_array()" intext:"mysql_query()" {q}',
    'intext:"Error Executing Database Query." intext:"SQL" {q}',
    # ── Tier 1 : PDO erreurs confirmées ───────────────────────────────────
    'inurl:.php?id= intext:"SQLSTATE[42000]: Syntax error" {q}',
    'intext:"PDOException: SQLSTATE" {q}',
    'intext:"PDO::query(): SQLSTATE" {q}',
    'intext:"SQLSTATE[HY000]" intext:"query" {q}',
    # ── Tier 1 : PostgreSQL erreurs confirmées ────────────────────────────
    'inurl:.php?id= intext:"PostgreSQL query failed: ERROR" {q}',
    'intext:"pg_query(): Query failed:" {q}',
    'intext:"pg_exec(): Query failed:" {q}',
    'inurl:id= intext:"unterminated quoted string at or near" {q}',
    'intext:"ERROR: syntax error at or near" {q}',
    # ── Tier 1 : MSSQL / SQL Server erreurs confirmées ───────────────────
    'inurl:id= intext:"Microsoft OLE DB Provider for SQL Server" {q}',
    'inurl:id= intext:"Unclosed quotation mark after the character string" {q}',
    'intext:"[Microsoft][ODBC SQL Server Driver]" {q}',
    'intext:"[Microsoft][SQL Native Client][SQL Server]" {q}',
    'intext:"Incorrect syntax near" intext:"SQL" {q}',
    'intext:"Warning: mssql_query()" {q}',
    'inurl:.asp?id= intext:"Syntax error" intext:"query" {q}',
    'inurl:.aspx?id= intext:"SqlException" {q}',
    # ── Tier 1 : Oracle erreurs confirmées ───────────────────────────────
    'inurl:id= intext:"ORA-01756: quoted string not properly terminated" {q}',
    'inurl:.php?id= intext:"ORA-00921: unexpected end of SQL command" {q}',
    'intext:"ORA-00933: SQL command not properly ended" {q}',
    'intext:"ORA-00907: missing right parenthesis" {q}',
    'intext:"ORA-00936: missing expression" {q}',
    # ── Tier 1 : SQLite erreurs confirmées ───────────────────────────────
    'intext:"SQLite3::query(): Unable to prepare statement" {q}',
    'intext:"Warning: SQLite3::exec()" intext:"syntax error" {q}',
    'intext:"SQLiteException: no such table" {q}',
    # ── Tier 2 : dumps SQL exposés ────────────────────────────────────────
    'filetype:sql intext:"phpMyAdmin SQL Dump" {q}',
    'filetype:sql "INSERT INTO" intext:"password" {q}',
    'ext:sql inurl:backup intext:"CREATE TABLE" {q}',
    'intitle:"index of" filetype:sql {q}',
    'filetype:sql "INSERT INTO" intext:"users" {q}',
    'intitle:"index of" "*.sql" {q}',
]

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


def generate_dorks(keywords: list[str], domain: str | None = None) -> list[str]:
    dorks: list[str] = []
    for keyword in keywords:
        for template in SQLI_TEMPLATES:
            dorks.append(build_dork(keyword, template, domain))
    return dorks


def save_dorks(dorks: list[str], output_path: Path) -> None:
    output_path.write_text("\n".join(dorks) + "\n", encoding="utf-8")


def run_generator(
    input_path: Path,
    output_path: Path | None = None,
    domain: str | None = None,
) -> tuple[int, Path]:
    if output_path is None:
        stem = input_path.stem.removesuffix("_keywords")
        output_path = input_path.with_name(f"{stem}_dorks.txt")

    keywords = load_lines(input_path)
    dorks = generate_dorks(keywords, domain=domain)
    save_dorks(dorks, output_path)

    template_count = len(SQLI_TEMPLATES)
    print(
        f"{len(keywords)} keywords × {template_count} dorktypes "
        f"= {len(dorks)} dorks SQL HQ"
    )
    if domain:
        print(f"Domaine : {domain}")
    print(f"Sauvegardé : {output_path}")

    return len(dorks), output_path


if __name__ == "__main__":
    from gui import main as gui_main

    gui_main()
