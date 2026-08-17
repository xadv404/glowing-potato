#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Google dorks SQLi — 1 keyword = 1 dork (pattern adapté automatiquement)
SQLI_TEMPLATES = [
    # Paramètres URL
    "inurl:id= {q}",
    "inurl:pid= {q}",
    "inurl:cat= {q}",
    "inurl:category= {q}",
    "inurl:page= {q}",
    "inurl:sid= {q}",
    "inurl:uid= {q}",
    "inurl:product_id= {q}",
    "inurl:item_id= {q}",
    "inurl:news_id= {q}",
    "inurl:article_id= {q}",
    "inurl:view= {q}",
    "inurl:num= {q}",
    "inurl:query= {q}",
    "inurl:search= {q}",
    # Pages PHP
    "inurl:index.php?id= {q}",
    "inurl:product.php?id= {q}",
    "inurl:article.php?id= {q}",
    "inurl:news.php?id= {q}",
    "inurl:page.php?id= {q}",
    "inurl:view.php?id= {q}",
    "inurl:category.php?id= {q}",
    "inurl:show.php?id= {q}",
    "inurl:detail.php?id= {q}",
    "inurl:gallery.php?id= {q}",
    "inurl:download.php?id= {q}",
    "inurl:profile.php?id= {q}",
    "inurl:shop.php?id= {q}",
    "inurl:games.php?id= {q}",
    "inurl:main.php?id= {q}",
    "inurl:sql.php?id= {q}",
    "inurl:buy.php?category= {q}",
    "inurl:trainers.php?id= {q}",
    "inurl:search.php?q= {q}",
    "inurl:.php?id= {q}",
    'inurl:".php?cat=" {q}',
    "allinurl:index.php?id= {q}",
    "allinurl:product.php?id= {q}",
    "allinurl:article.php?id= {q}",
    # Error-based
    'inurl:id= intext:"You have an error in your SQL syntax" {q}',
    'inurl:id= intext:"mysql_fetch_array()" {q}',
    'inurl:id= intext:"mysql_fetch_assoc()" {q}',
    'inurl:id= intext:"mysql_num_rows()" {q}',
    'inurl:id= intext:"Warning: mysql_query()" {q}',
    'inurl:cat= intext:"You have an error in your SQL syntax" {q}',
    'inurl:page= intext:"You have an error in your SQL syntax" {q}',
    'intext:"You have an error in your SQL syntax" {q}',
    'intext:"mysql_fetch_array()" {q}',
    'intext:"select * from" {q}',
    'intext:"ORA-00933: SQL command not properly ended" {q}',
    'intext:"Unclosed quotation mark" {q}',
    # Combos PHP + SQLi
    "filetype:php inurl:id= {q}",
    "filetype:php inurl:cat= {q}",
    "filetype:php inurl:index.php?id= {q}",
    "filetype:php inurl:product.php?id= {q}",
    'filetype:php intext:"mysql_fetch_array()" {q}',
    'filetype:php intext:"You have an error in your SQL syntax" {q}',
    'inurl:.php?id= intext:"mysql" {q}',
    # Fichiers sensibles SQL
    'filetype:sql "backup" {q}',
    'filetype:sql "dump" {q}',
    'filetype:env "DB_PASSWORD" {q}',
    'filetype:env "MYSQL" {q}',
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


def pick_sqli_template(keyword: str) -> str:
    return SQLI_TEMPLATES[hash(keyword) % len(SQLI_TEMPLATES)]


def build_dork(keyword: str, domain: str | None = None) -> str:
    q = quote_keyword(keyword)
    dork = pick_sqli_template(keyword).format(q=q)
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
            "Génère 1 Google dork SQLi par keyword. "
            "Le dorktype est choisi automatiquement parmi 62 patterns."
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
