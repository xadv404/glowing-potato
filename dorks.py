#!/usr/bin/env python3
import argparse
import sys
from itertools import product
from pathlib import Path

DORK_TYPES = ("generic", "sqli", "all")

FILE_TYPES = ["pdf", "doc", "docx", "xls", "xlsx", "csv", "sql", "txt", "xml", "json", "env", "log", "bak", "conf", "cfg"]

INURL_PATTERNS = [
    "admin", "login", "dashboard", "backup", "config", "upload", "api",
    "debug", "console", "phpmyadmin", "wp-admin", "wp-content",
    "database", "db", "secret", "password", "token", "key",
]

INTITLE_PATTERNS = [
    "index of", "login", "admin", "dashboard", "password",
    "confidential", "backup", "database", "error",
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

# --- SQLi dorktypes ---

SQLI_PARAMS = [
    "id=", "pid=", "cat=", "category=", "page=", "sid=", "uid=",
    "user_id=", "product_id=", "item_id=", "news_id=", "article_id=",
    "num=", "view=", "dir=", "file=", "action=", "cmd=", "query=",
    "search=", "keyword=", "type=", "module=", "section=", "game_id=",
    "staff_id=", "channel_id=", "item_id=", "decl_id=", "pageid=",
]

SQLI_PAGES = [
    "index.php?id=", "product.php?id=", "article.php?id=", "news.php?id=",
    "page.php?id=", "view.php?id=", "category.php?id=", "show.php?id=",
    "detail.php?id=", "gallery.php?id=", "download.php?id=", "profile.php?id=",
    "shop.php?id=", "games.php?id=", "sql.php?id=", "main.php?id=",
    "newsDetail.php?id=", "readnews.php?id=", "article.php?ID=",
    "buy.php?category=", "trainers.php?id=", "play_old.php?id=",
    "page.php?file=", "newsitem.php?num=", "top10.php?cat=",
    "view_product.php?id=", "productinfo.php?id=", "memberInfo.php?id=",
    "announce.php?id=", "material.php?id=", "story.php?id=",
]

SQLI_ERRORS = [
    "You have an error in your SQL syntax",
    "mysql_fetch_array()",
    "mysql_fetch_assoc()",
    "mysql_num_rows()",
    "Warning: mysql_query()",
    "mysqli_fetch_array()",
    "PostgreSQL query failed",
    "ORA-01756",
    "Microsoft OLE DB Provider for SQL Server",
    "Unclosed quotation mark",
    "quoted string not properly terminated",
    "SQL syntax",
    "Error Executing Database Query",
    "Error Occurred While Processing Request",
    "Warning: pg_exec()",
]

SQLI_PARAM_TEMPLATES = [
    "inurl:{param} {keyword}",
    "inurl:{param} intext:{keyword}",
    'inurl:{param} "{keyword}"',
    "filetype:php inurl:{param} {keyword}",
    "ext:php inurl:{param} {keyword}",
]

SQLI_PAGE_TEMPLATES = [
    "inurl:{page} {keyword}",
    "allinurl:{page} {keyword}",
    'inurl:{page} intext:"{keyword}"',
    "filetype:php inurl:{page} {keyword}",
]

SQLI_ERROR_TEMPLATES = [
    'inurl:id= intext:"{error}" {keyword}',
    'inurl:cat= intext:"{error}" {keyword}',
    'inurl:page= intext:"{error}" {keyword}',
    'intext:"{error}" {keyword}',
    'intext:"{error}" intext:{keyword}',
    'filetype:php intext:"{error}" {keyword}',
]

SQLI_COMBO_TEMPLATES = [
    'inurl:{param} intext:"{error}" {keyword}',
    'inurl:{page} intext:"{error}" {keyword}',
    'filetype:php inurl:{param} intext:"{error}" {keyword}',
]

SQLI_SITE_TEMPLATES = [
    "site:{domain} inurl:id= {keyword}",
    "site:{domain} inurl:cat= {keyword}",
    "site:{domain} inurl:page= {keyword}",
    "site:{domain} inurl:index.php?id= {keyword}",
    "site:{domain} inurl:product.php?id= {keyword}",
    "site:{domain} inurl:article.php?id= {keyword}",
    "site:{domain} inurl:news.php?id= {keyword}",
    'site:{domain} inurl:id= intext:"You have an error in your SQL syntax" {keyword}',
    'site:{domain} inurl:id= intext:"mysql_fetch_array()" {keyword}',
    "site:{domain} filetype:php inurl:id= {keyword}",
    "site:{domain} filetype:php inurl:cat= {keyword}",
    'site:{domain} intext:"SQL syntax" {keyword}',
]

SQLI_FILE_TEMPLATES = [
    'filetype:sql "{keyword}"',
    'filetype:sql intext:{keyword}',
    'filetype:sql "dump" {keyword}',
    'filetype:sql "backup" {keyword}',
    'filetype:sql "insert into" {keyword}',
    'filetype:env "DB_PASSWORD" {keyword}',
    'filetype:env "MYSQL" {keyword}',
    'filetype:log intext:"sql" {keyword}',
    'filetype:bak intext:"sql" {keyword}',
    'filetype:php inurl:config intext:{keyword}',
    'filetype:php inurl:db intext:{keyword}',
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


def generate_generic_dorks(
    keywords: list[str],
    domains: list[str],
    include_filetypes: bool = True,
    include_inurl: bool = True,
    include_intitle: bool = True,
    include_site: bool = True,
) -> set[str]:
    dorks: set[str] = set()

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


def generate_sqli_dorks(
    keywords: list[str],
    domains: list[str],
    include_site: bool = True,
) -> set[str]:
    dorks: set[str] = set()
    top_params = SQLI_PARAMS[:20]
    top_pages = SQLI_PAGES[:20]
    top_errors = SQLI_ERRORS[:10]

    for keyword in keywords:
        for param, template in product(top_params, SQLI_PARAM_TEMPLATES):
            dorks.add(template.format(param=param, keyword=keyword))

        for page, template in product(top_pages, SQLI_PAGE_TEMPLATES):
            dorks.add(template.format(page=page, keyword=keyword))

        for error, template in product(SQLI_ERRORS, SQLI_ERROR_TEMPLATES):
            dorks.add(template.format(error=error, keyword=keyword))

        for param, error in product(top_params[:10], top_errors):
            dorks.add(
                SQLI_COMBO_TEMPLATES[0].format(param=param, error=error, keyword=keyword)
            )

        for page, error in product(top_pages[:8], top_errors[:6]):
            dorks.add(
                SQLI_COMBO_TEMPLATES[1].format(page=page, error=error, keyword=keyword)
            )

        for param, error in product(top_params[:6], top_errors[:4]):
            dorks.add(
                SQLI_COMBO_TEMPLATES[2].format(param=param, error=error, keyword=keyword)
            )

        for template in SQLI_FILE_TEMPLATES:
            dorks.add(template.format(keyword=keyword))

        if include_site and domains:
            for domain, template in product(domains, SQLI_SITE_TEMPLATES):
                dorks.add(template.format(domain=domain, keyword=keyword))

    return dorks


def generate_dorks(
    keywords: list[str],
    domains: list[str] | None = None,
    dork_types: list[str] | None = None,
    include_filetypes: bool = True,
    include_inurl: bool = True,
    include_intitle: bool = True,
    include_site: bool = True,
) -> set[str]:
    domains = domains or []
    dork_types = dork_types or ["generic"]
    use_generic = "all" in dork_types or "generic" in dork_types
    use_sqli = "all" in dork_types or "sqli" in dork_types

    dorks: set[str] = set()

    if use_generic:
        dorks.update(
            generate_generic_dorks(
                keywords,
                domains,
                include_filetypes=include_filetypes,
                include_inurl=include_inurl,
                include_intitle=include_intitle,
                include_site=include_site,
            )
        )

    if use_sqli:
        dorks.update(
            generate_sqli_dorks(
                keywords,
                domains,
                include_site=include_site,
            )
        )

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
            "Supporte les dorktypes generic et sqli."
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
        "-t",
        "--type",
        choices=DORK_TYPES,
        default="sqli",
        help="Type de dorks : generic, sqli ou all (défaut: sqli)",
    )
    parser.add_argument(
        "--no-filetypes",
        action="store_true",
        help="Désactive les dorks filetype/ext (generic uniquement)",
    )
    parser.add_argument(
        "--no-inurl",
        action="store_true",
        help="Désactive les dorks inurl (generic uniquement)",
    )
    parser.add_argument(
        "--no-intitle",
        action="store_true",
        help="Désactive les dorks intitle (generic uniquement)",
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
    dork_types: list[str] | None = None,
    include_filetypes: bool = True,
    include_inurl: bool = True,
    include_intitle: bool = True,
    include_site: bool = True,
) -> tuple[int, Path]:
    if output_path is None:
        suffix = (dork_types or ["sqli"])[0]
        output_path = input_path.with_name(f"{input_path.stem}_{suffix}_dorks.txt")

    keywords = load_lines(input_path)
    domains = load_lines(domains_path) if domains_path else []

    print(f"{len(keywords)} keywords chargés depuis {input_path}")
    print(f"Dorktypes : {', '.join(dork_types or ['sqli'])}")
    if domains:
        print(f"{len(domains)} domaines chargés depuis {domains_path}")

    dorks = generate_dorks(
        keywords,
        domains=domains,
        dork_types=dork_types,
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
            dork_types=[args.type],
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
