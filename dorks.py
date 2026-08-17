#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Google dorks SQLi — 1 keyword = 1 dork
# Sources: CVE-2026 advisories, GHDB 2026, SecOps-Google-Dork-Collection
# {q} = keyword (guillemets si plusieurs mots)

SQLI_CVE_2026_TEMPLATES = [
    # CVE-2026-9082 — Drupal Core PostgreSQL SQLi (SA-CORE-2026-004)
    'inurl:"/user/login?_format=json" {q}',
    'inurl:"/jsonapi/node/" {q}',
    'inurl:jsonapi intext:"Drupal" {q}',
    # CVE-2026-56292 — AcyMailing Joomla SQLi
    'inurl:"index.php?option=com_acym" {q}',
    'inurl:option=com_acym {q}',
    '"Powered by AcyMailing" {q}',
    'inurl:"index.php?option=com_acym&ctrl=cron" {q}',
    # CVE-2026-42031 — CKAN datastore_search_sql SQLi
    'intitle:"CKAN" {q}',
    'inurl:"/api/action/datastore_search_sql" {q}',
    'inurl:"/api/action/status_show" intitle:"CKAN" {q}',
    # CVE-2026-26980 — Ghost CMS Content API SQLi
    '"data-ghost=" {q}',
    'inurl:"/ghost/api/content/" {q}',
    # CVE-2026-69083 — SiYuan SQLi
    'inurl:"/api/search/fullTextSearchAssetContent" {q}',
    'intitle:"SiYuan" {q}',
    # GHDB 2026 — paramètres SQLi (SecOps / DorkPlus)
    "inurl:id= {q}",
    "inurl:pid= {q}",
    "inurl:cat= {q}",
    "inurl:category= {q}",
    "inurl:sid= {q}",
    "inurl:dir= {q}",
    "inurl:index.php?id= {q}",
    "inurl:product.php?id= {q}",
    "inurl:article.php?id= {q}",
    "inurl:page.php?id= {q}",
    "inurl:view.php?id= {q}",
    "inurl:news.php?id= {q}",
    "inurl:category.php?id= {q}",
    "inurl:.php?id= {q}",
    'inurl:".php?cat=" {q}',
    "allinurl:index.php?id= {q}",
    # GHDB 2026 — error-based SQLi
    'inurl:id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:id= intext:"mysql_fetch_array()" {q}',
    'inurl:id= intext:"mysql_fetch_assoc()" {q}',
    'inurl:id= intext:"Warning: mysql_query()" {q}',
    'intext:"You have an error in your SQL syntax" {q}',
    'intext:"SQL syntax" intext:"error" {q}',
    'intext:"database error" {q}',
    'intext:"ORA-00933" {q}',
    'intext:"Microsoft OLE DB Provider for SQL Server" {q}',
    'intext:"Unclosed quotation mark" {q}',
    # GHDB 2026 — combos
    "filetype:php inurl:id= {q}",
    'filetype:php intext:"mysql_fetch_array()" {q}',
    'inurl:.php?id= intext:"mysql" {q}',
    'filetype:sql "backup" {q}',
    'filetype:env "DB_PASSWORD" {q}',
    # SecOps 2026 — SQLi-prone params (condensé)
    "inurl:id= inurl:cat= inurl:action= {q}",
    'inurl:"error" intext:"SQL syntax" {q}',
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
    return SQLI_CVE_2026_TEMPLATES[hash(keyword) % len(SQLI_CVE_2026_TEMPLATES)]


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
            "Génère 1 Google dork SQLi par keyword (CVE 2026 + GHDB). "
            "Lit un txt (1 keyword/ligne), écrit 1 dork/ligne."
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
    print(f"{len(SQLI_CVE_2026_TEMPLATES)} dorktypes CVE/GHDB 2026 en rotation")
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
