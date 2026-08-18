#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# HQ Google dorks SQL — 1 keyword = 1 dork
# Curated: param + error combos (highest signal), CVE SQL 2026, GHDB/Box Piper 2026
# Sources: DorkFinder, Box Piper 2026, SecOps-Google-Dork-Collection, CVE advisories
# {q} = keyword

SQLI_HQ_TEMPLATES = [
    # ── Tier 1 : param + erreur SQL (meilleur signal) ──
    'inurl:".php?id=" intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:"index.php?id=" intext:"Warning: mysql_num_rows()" {q}',
    'inurl:index.php?id= intext:"mysql_fetch_array" {q}',
    'inurl:"id=" intext:"MySQL Error: 1064" {q}',
    'inurl:id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:id= intext:"mysql_fetch_array()" {q}',
    'inurl:id= intext:"mysql_fetch_assoc()" {q}',
    'inurl:id= intext:"Warning: mysql_query()" {q}',
    'inurl:".php?catid=" intext:"Warning: mysql_fetch_array()" {q}',
    'inurl:"page.php?id=" intext:"mysql_num_rows()" {q}',
    'inurl:product.php?id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:article.php?id= intext:"mysql_fetch_assoc()" {q}',
    'inurl:news.php?id= intext:"SQL syntax" {q}',
    'inurl:category.php?id= intext:"SQL syntax" {q}',
    'inurl:view.php?id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:advsearch.php?module= intext:"sql syntax" {q}',
    'allinurl:index.php?id= intext:"You have an error in your SQL syntax" {q}',
    'filetype:php inurl:id= intext:"You have an error in your SQL syntax" {q}',
    'filetype:php inurl:id= intext:"mysql_fetch_array()" {q}',
    # ── Tier 1 : erreurs par SGBD ──
    'inurl:.php?id= intext:"PostgreSQL query failed: ERROR" {q}',
    'inurl:id= intext:"unterminated quoted string at or near" {q}',
    'inurl:id= intext:"ORA-01756: quoted string not properly terminated" {q}',
    'inurl:.php?id= intext:"ORA-00921: unexpected end of SQL command" {q}',
    'inurl:id= intext:"Microsoft OLE DB Provider for SQL Server" {q}',
    'inurl:id= intext:"Unclosed quotation mark" intext:"SQL Server" {q}',
    'inurl:id= intext:"SQLSTATE" {q}',
    'intext:"Error Executing Database Query." intext:"SQL" {q}',
    'intext:"mysql_num_rows()" intext:"mysql_fetch_array()" intext:"mysql_query()" {q}',
    'inurl:"error" intext:"SQL syntax" intext:"database error" {q}',
    # ── Tier 2 : CVE SQL 2026 ──
    'inurl:"/api/action/datastore_search_sql" {q}',
    'inurl:"/user/login?_format=json" intext:"SQLSTATE" {q}',
    'inurl:"/jsonapi/node/" intext:"SQL" {q}',
    'inurl:"index.php?option=com_acym" intext:"sql" {q}',
    # ── Tier 2 : pages PHP SQLi classiques (GHDB) ──
    "inurl:index.php?id= {q}",
    "inurl:product.php?id= {q}",
    "inurl:article.php?id= {q}",
    "inurl:trainers.php?id= {q}",
    "inurl:buy.php?category= {q}",
    "inurl:games.php?id= {q}",
    "inurl:sql.php?id= {q}",
    "inurl:page.php?file= {q}",
    # ── Tier 3 : dumps / fichiers SQL exposés ──
    'filetype:sql intext:"phpMyAdmin SQL Dump" {q}',
    'filetype:sql "INSERT INTO" intext:"password" {q}',
    'ext:sql inurl:backup intext:"CREATE TABLE" {q}',
    'intitle:"index of" filetype:sql {q}',
    # ── Tier 3 : SecOps 2026 — params SQLi condensés ──
    'inurl:id= | inurl:cat= | inurl:page= intext:"SQL syntax" {q}',
    'inurl:id= | inurl:pid= | inurl:category= intext:"database error" {q}',
]

# Alias pour la GUI
SQLI_SQL_TEMPLATES = SQLI_HQ_TEMPLATES


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


def pick_template(keyword: str) -> str:
    return SQLI_HQ_TEMPLATES[hash(keyword) % len(SQLI_HQ_TEMPLATES)]


def build_dork(keyword: str, domain: str | None = None) -> str:
    q = quote_keyword(keyword)
    dork = pick_template(keyword).format(q=q)
    if domain:
        return f"site:{domain} {dork}"
    return dork


def generate_dorks(keywords: list[str], domain: str | None = None) -> list[str]:
    return [build_dork(keyword, domain) for keyword in keywords]


def save_dorks(dorks: list[str], output_path: Path) -> None:
    output_path.write_text("\n".join(dorks) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Génère 1 Google dork SQL HQ par keyword. "
            "Combos param+erreur, CVE SQL 2026, GHDB curated."
        )
    )
    parser.add_argument(
        "input",
        help="Fichier txt de keywords (1 par ligne, obligatoire)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Fichier de sortie (défaut: {input}_sqli_dorks.txt)",
    )
    parser.add_argument(
        "-d",
        "--domain",
        help="Domaine cible pour site: (ex: example.com)",
    )
    return parser.parse_args()


def run_generator(
    input_path: Path,
    output_path: Path | None = None,
    domain: str | None = None,
) -> tuple[int, Path]:
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_sqli_dorks.txt")

    keywords = load_lines(input_path)
    dorks = generate_dorks(keywords, domain=domain)
    save_dorks(dorks, output_path)

    print(f"{len(keywords)} keywords -> {len(dorks)} dorks SQL HQ (1 par keyword)")
    print(f"{len(SQLI_HQ_TEMPLATES)} dorktypes HQ en rotation")
    if domain:
        print(f"Domaine : {domain}")
    print(f"Sauvegardé : {output_path}")

    return len(dorks), output_path


def main() -> None:
    args = parse_args()

    try:
        run_generator(
            input_path=Path(args.input),
            output_path=Path(args.output) if args.output else None,
            domain=args.domain,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
