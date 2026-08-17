#!/usr/bin/env python3
import argparse
import sys
from itertools import product
from pathlib import Path

FILE_TYPES = ["pdf", "doc", "docx", "xls", "xlsx", "csv", "sql", "txt", "xml", "json", "env", "log", "bak", "conf", "cfg"]

INURL_PATTERNS = [
    "admin",
    "login",
    "dashboard",
    "backup",
    "config",
    "upload",
    "api",
    "debug",
    "console",
    "phpmyadmin",
    "wp-admin",
    "wp-content",
    "database",
    "db",
    "secret",
    "password",
    "token",
    "key",
]

INTITLE_PATTERNS = [
    "index of",
    "login",
    "admin",
    "dashboard",
    "password",
    "confidential",
    "backup",
    "database",
    "error",
]

BASIC_TEMPLATES = [
    'intitle:"{keyword}"',
    "inurl:{keyword}",
    "intext:{keyword}",
    'allintext:"{keyword}"',
    '"{keyword}"',
    "intitle:{keyword} inurl:{keyword}",
]

FILETYPE_TEMPLATES = [
    'filetype:{ext} "{keyword}"',
    'filetype:{ext} intext:{keyword}',
    'filetype:{ext} intitle:{keyword}',
]

INURL_TEMPLATES = [
    'inurl:{pattern} intext:{keyword}',
    'inurl:{pattern} "{keyword}"',
    'inurl:{pattern} intitle:{keyword}',
]

INTITLE_TEMPLATES = [
    'intitle:"{pattern}" intext:{keyword}',
    'intitle:"{pattern}" {keyword}',
    'intitle:{pattern} filetype:pdf {keyword}',
]

SITE_TEMPLATES = [
    "site:{domain} {keyword}",
    'site:{domain} "{keyword}"',
    "site:{domain} intext:{keyword}",
    "site:{domain} inurl:{keyword}",
    'site:{domain} intitle:"{keyword}"',
    "site:{domain} filetype:pdf {keyword}",
    "site:{domain} filetype:doc {keyword}",
    "site:{domain} filetype:xls {keyword}",
    "site:{domain} inurl:admin {keyword}",
    "site:{domain} inurl:login {keyword}",
    "site:{domain} inurl:backup {keyword}",
    "site:{domain} inurl:config {keyword}",
    'site:{domain} intitle:"index of" {keyword}',
    "site:{domain} ext:sql {keyword}",
    "site:{domain} ext:env {keyword}",
    "site:{domain} ext:log {keyword}",
    "site:{domain} ext:bak {keyword}",
]


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
        raise ValueError(f"Aucune entrée trouvée dans {path}")

    return lines


def generate_dorks(
    keywords: list[str],
    domains: list[str] | None = None,
    include_filetypes: bool = True,
    include_inurl: bool = True,
    include_intitle: bool = True,
    include_site: bool = True,
) -> set[str]:
    dorks: set[str] = set()
    domains = domains or []

    for keyword in keywords:
        for template in BASIC_TEMPLATES:
            dorks.add(template.format(keyword=keyword))

        if include_filetypes:
            for ext, template in product(FILE_TYPES, FILETYPE_TEMPLATES):
                dorks.add(template.format(ext=ext, keyword=keyword))

        if include_inurl:
            for pattern, template in product(INURL_PATTERNS, INURL_TEMPLATES):
                dorks.add(template.format(pattern=pattern, keyword=keyword))

        if include_intitle:
            for pattern, template in product(INTITLE_PATTERNS, INTITLE_TEMPLATES):
                dorks.add(template.format(pattern=pattern, keyword=keyword))

        if include_site and domains:
            for domain, template in product(domains, SITE_TEMPLATES):
                dorks.add(template.format(domain=domain, keyword=keyword))

    return dorks


def save_dorks(dorks: set[str], output_path: Path) -> None:
    output_path.write_text(
        "\n".join(sorted(dorks)) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Génère des Google dorks à partir d'un fichier de keywords. "
            "Combine keywords avec des opérateurs (site, inurl, intitle, filetype...)."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="keywords.txt",
        help="Fichier txt de keywords (défaut: keywords.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="dorks.txt",
        help="Fichier de sortie (défaut: dorks.txt)",
    )
    parser.add_argument(
        "-d",
        "--domains",
        help="Fichier txt de domaines (1 par ligne) pour les dorks site:",
    )
    parser.add_argument(
        "--no-filetypes",
        action="store_true",
        help="Désactive les dorks filetype/ext",
    )
    parser.add_argument(
        "--no-inurl",
        action="store_true",
        help="Désactive les dorks inurl",
    )
    parser.add_argument(
        "--no-intitle",
        action="store_true",
        help="Désactive les dorks intitle",
    )
    parser.add_argument(
        "--no-site",
        action="store_true",
        help="Désactive les dorks site: même si un fichier domaines est fourni",
    )
    return parser.parse_args()


def run_generator(
    input_path: Path,
    output_path: Path | None = None,
    domains_path: Path | None = None,
    include_filetypes: bool = True,
    include_inurl: bool = True,
    include_intitle: bool = True,
    include_site: bool = True,
) -> tuple[int, Path]:
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_dorks.txt")

    keywords = load_lines(input_path)
    domains = load_lines(domains_path) if domains_path else []

    print(f"{len(keywords)} keywords chargés depuis {input_path}")
    if domains:
        print(f"{len(domains)} domaines chargés depuis {domains_path}")

    dorks = generate_dorks(
        keywords,
        domains=domains,
        include_filetypes=include_filetypes,
        include_inurl=include_inurl,
        include_intitle=include_intitle,
        include_site=include_site and bool(domains),
    )
    save_dorks(dorks, output_path)

    print(f"{len(dorks)} dorks générés -> {output_path}")
    return len(dorks), output_path


def main() -> None:
    args = parse_args()

    try:
        run_generator(
            input_path=Path(args.input),
            output_path=Path(args.output),
            domains_path=Path(args.domains) if args.domains else None,
            include_filetypes=not args.no_filetypes,
            include_inurl=not args.no_inurl,
            include_intitle=not args.no_intitle,
            include_site=not args.no_site,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
