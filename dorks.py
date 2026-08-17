#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

DORK_TYPES = ("sqli", "login", "lfi", "generic", "google")

# Patterns Google dorks reconnus (sources: dorkplus, trixsec, neospl0it/Dorks)
# {q} = keyword (entre guillemets si plusieurs mots)
DORK_PATTERNS: dict[str, list[str]] = {
    "sqli": [
        "inurl:index.php?id= {q}",
        "inurl:product.php?id= {q}",
        "inurl:article.php?id= {q}",
        "inurl:page.php?id= {q}",
        "inurl:view.php?id= {q}",
        "inurl:category.php?id= {q}",
        "inurl:news.php?id= {q}",
        "inurl:.php?id= {q}",
        'inurl:".php?cat=" {q}',
        "inurl:search.php?q= {q}",
        "filetype:php inurl:id= {q}",
        'inurl:id= intext:"You have an error in your SQL syntax" {q}',
        'inurl:id= intext:"mysql_fetch_array()" {q}',
    ],
    "login": [
        "inurl:login.php {q}",
        "inurl:admin/login.php {q}",
        "inurl:admin intitle:login {q}",
        'intitle:"admin login" {q}',
        "inurl:wp-admin {q}",
        "inurl:administrator/index.php {q}",
        "inurl:admin intext:password {q}",
    ],
    "lfi": [
        "inurl:page= {q}",
        "inurl:file= {q}",
        "inurl:include= {q}",
        "inurl:path= {q}",
        "inurl:read.php?file= {q}",
        'inurl:page= intext:"Warning: include" {q}',
    ],
    "generic": [
        'intitle:"index of" {q}',
        'filetype:sql "backup" {q}',
        'filetype:env "DB_PASSWORD" {q}',
        'intext:"password" filetype:txt {q}',
        "inurl:backup {q}",
        "inurl:config {q}",
        'filetype:log intext:password {q}',
    ],
    "google": [
        "inurl:admin {q}",
        "inurl:api {q}",
        "inurl:upload {q}",
        "filetype:pdf {q}",
        "filetype:sql {q}",
    ],
}


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


def pick_pattern(keyword: str, dork_type: str) -> str:
    patterns = DORK_PATTERNS.get(dork_type)
    if not patterns:
        raise ValueError(f"Dorktype inconnu : {dork_type}")
    return patterns[hash(keyword) % len(patterns)]


def build_dork(keyword: str, dork_type: str, domain: str | None = None) -> str:
    q = quote_keyword(keyword)
    pattern = pick_pattern(keyword, dork_type)
    dork = pattern.format(q=q)

    if domain:
        return f"site:{domain} {dork}"
    return dork


def generate_dorks(
    keywords: list[str],
    dork_type: str = "sqli",
    domain: str | None = None,
) -> list[str]:
    return [build_dork(keyword, dork_type, domain) for keyword in keywords]


def save_dorks(dorks: list[str], output_path: Path) -> None:
    output_path.write_text("\n".join(dorks) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Génère 1 Google dork par keyword (patterns reconnus). "
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
        help="Fichier de sortie (défaut: {input}_dorks.txt)",
    )
    parser.add_argument(
        "-d",
        "--domain",
        help="Domaine cible pour site: (ex: example.com)",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=DORK_TYPES,
        default="sqli",
        help="Type de dork (défaut: sqli)",
    )
    return parser.parse_args()


def run_generator(
    input_path: Path,
    output_path: Path | None = None,
    domain: str | None = None,
    dork_type: str = "sqli",
) -> tuple[int, Path]:
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_dorks.txt")

    keywords = load_lines(input_path)
    dorks = generate_dorks(keywords, dork_type=dork_type, domain=domain)
    save_dorks(dorks, output_path)

    print(f"{len(keywords)} keywords -> {len(dorks)} dorks Google")
    print(f"Dorktype : {dork_type}")
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
            dork_type=args.type,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
