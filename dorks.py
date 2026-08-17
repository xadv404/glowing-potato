#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Google dorks SQLi — 100% SQL (params, erreurs, dumps, CVE SQL 2026)
# Chaque template contient un opérateur/mot-clé SQL explicite
# {q} = keyword

SQLI_SQL_TEMPLATES = [
    # CVE-2026 SQLi
    'inurl:"/api/action/datastore_search_sql" {q}',
    'inurl:"/user/login?_format=json" intext:"SQL" {q}',
    'inurl:"/jsonapi/node/" intext:"sql" {q}',
    'inurl:option=com_acym intext:"sql" {q}',
    'inurl:"index.php?option=com_acym" intext:"SQL" {q}',
    # Paramètres SQL injectables
    "inurl:id= {q}",
    "inurl:pid= {q}",
    "inurl:cat= intext:sql {q}",
    "inurl:category= intext:sql {q}",
    "inurl:sid= {q}",
    "inurl:sql.php?id= {q}",
    "inurl:index.php?id= {q}",
    "inurl:product.php?id= {q}",
    "inurl:article.php?id= {q}",
    "inurl:page.php?id= {q}",
    "inurl:view.php?id= {q}",
    "inurl:news.php?id= {q}",
    "inurl:category.php?id= {q}",
    "inurl:.php?id= {q}",
    'inurl:".php?cat=" intext:"SQL syntax" {q}',
    "allinurl:index.php?id= {q}",
    "allinurl:product.php?id= {q}",
    # Erreurs SQL (MySQL)
    'inurl:id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:id= intext:"mysql_fetch_array()" {q}',
    'inurl:id= intext:"mysql_fetch_assoc()" {q}',
    'inurl:id= intext:"mysql_num_rows()" {q}',
    'inurl:id= intext:"Warning: mysql_query()" {q}',
    'intext:"You have an error in your SQL syntax" {q}',
    'intext:"mysql_fetch_array()" {q}',
    'intext:"mysql_fetch_assoc()" {q}',
    'intext:"mysql_query()" {q}',
    'intext:"select * from" {q}',
    'intext:"SQL syntax" {q}',
    'intext:"SQL syntax" intext:"error" {q}',
    'intext:"database error" {q}',
    # Erreurs SQL (PostgreSQL / MSSQL / Oracle)
    'intext:"PostgreSQL query failed" {q}',
    'intext:"SQLSTATE" {q}',
    'intext:"ORA-00933" {q}',
    'intext:"Microsoft OLE DB Provider for SQL Server" {q}',
    'intext:"Unclosed quotation mark" intext:"SQL Server" {q}',
    'intext:"Error Executing Database Query" {q}',
    # Combos PHP + SQL
    "filetype:php inurl:id= intext:sql {q}",
    'filetype:php intext:"mysql_fetch_array()" {q}',
    'filetype:php intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?id= intext:"mysql" {q}',
    'inurl:cat= intext:"SQL syntax" {q}',
    'inurl:page= intext:"SQL syntax" {q}',
    # Fichiers / dumps SQL
    'filetype:sql "INSERT INTO" {q}',
    'filetype:sql "backup" {q}',
    'filetype:sql intext:"password" {q}',
    'filetype:sql "dump" {q}',
    'ext:sql inurl:backup {q}',
    'ext:sql intext:"mysql" {q}',
    'intitle:"index of" filetype:sql {q}',
    'intext:"phpMyAdmin SQL Dump" {q}',
    # SecOps 2026 — params + SQL errors
    'inurl:id= inurl:cat= intext:"SQL syntax" {q}',
    'inurl:"error" intext:"SQL syntax" {q}',
    'inurl:"error" intext:"database error" {q}',
]


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
    return SQLI_SQL_TEMPLATES[hash(keyword) % len(SQLI_SQL_TEMPLATES)]


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
            "Génère 1 Google dork SQL par keyword. "
            "Uniquement SQL : params, erreurs, dumps, CVE SQL 2026."
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

    print(f"{len(keywords)} keywords -> {len(dorks)} dorks SQLi (1 par keyword)")
    print(f"{len(SQLI_SQL_TEMPLATES)} dorktypes SQL en rotation")
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
