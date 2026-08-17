#!/usr/bin/env python3
import argparse
import sys
from itertools import product
from pathlib import Path
from urllib.parse import quote_plus

DORK_TYPES = ("google", "sqli", "generic", "all")
GOOGLE_SEARCH_URL = "https://www.google.com/search?q="

FILE_TYPES = ["pdf", "doc", "xls", "csv", "sql", "txt", "xml", "json", "env", "log", "bak", "conf"]

INURL_PATTERNS = [
    "admin", "login", "dashboard", "backup", "config", "upload", "api",
    "debug", "phpmyadmin", "wp-admin", "database", "password", "token",
]

INTITLE_PATTERNS = [
    "index of", "login", "admin", "dashboard", "password", "backup", "database",
]

# --- Pure Google dorks (sans keyword) ---

PURE_GOOGLE_DORKS = [
    'inurl:admin intitle:login',
    'inurl:login.php',
    'inurl:admin.php',
    'inurl:admin/login',
    'inurl:administrator',
    'inurl:wp-admin',
    'inurl:wp-login.php',
    'inurl:phpmyadmin',
    'intitle:"index of"',
    'intitle:"index of" "parent directory"',
    'intitle:"index of" filetype:sql',
    'intitle:"index of" filetype:env',
    'intitle:"index of" filetype:log',
    'intitle:"index of" filetype:bak',
    'intitle:"index of" filetype:cfg',
    'filetype:sql "insert into"',
    'filetype:sql "dump"',
    'filetype:sql "backup"',
    'filetype:env "DB_PASSWORD"',
    'filetype:env "MYSQL"',
    'filetype:env "API_KEY"',
    'filetype:log intext:password',
    'filetype:pdf intext:confidential',
    'filetype:xls intext:password',
    'filetype:csv intext:email',
    'ext:sql intext:password',
    'ext:env intext:secret',
    'ext:bak intext:backup',
    'ext:old intext:password',
    'inurl:backup filetype:sql',
    'inurl:config filetype:env',
    'inurl:.git/config',
    'inurl:.env',
    'inurl:api intext:token',
    'inurl:api intext:secret',
    'intext:"password" filetype:txt',
    'intext:"username" intext:"password" filetype:txt',
    'intitle:login intext:password',
    'inurl:ftp intext:login',
    'inurl:shell intext:cmd',
]

PURE_SQLI_DORKS = [
    "inurl:id=",
    "inurl:pid=",
    "inurl:cat=",
    "inurl:category=",
    "inurl:page=",
    "inurl:sid=",
    "inurl:uid=",
    "inurl:product_id=",
    "inurl:item_id=",
    "inurl:news_id=",
    "inurl:article_id=",
    "inurl:view=",
    "inurl:dir=",
    "inurl:file=",
    "inurl:action=",
    "inurl:cmd=",
    "inurl:query=",
    "inurl:search=",
    "inurl:type=",
    "inurl:module=",
    "inurl:index.php?id=",
    "inurl:product.php?id=",
    "inurl:article.php?id=",
    "inurl:news.php?id=",
    "inurl:page.php?id=",
    "inurl:view.php?id=",
    "inurl:category.php?id=",
    "inurl:show.php?id=",
    "inurl:detail.php?id=",
    "inurl:gallery.php?id=",
    "inurl:download.php?id=",
    "inurl:profile.php?id=",
    "inurl:shop.php?id=",
    "inurl:games.php?id=",
    "inurl:sql.php?id=",
    "inurl:main.php?id=",
    "inurl:buy.php?category=",
    "inurl:trainers.php?id=",
    "inurl:page.php?file=",
    "inurl:newsitem.php?num=",
    "inurl:top10.php?cat=",
    "allinurl:index.php?id=",
    "allinurl:product.php?id=",
    "allinurl:article.php?id=",
    'inurl:id= intext:"You have an error in your SQL syntax"',
    'inurl:id= intext:"mysql_fetch_array()"',
    'inurl:id= intext:"mysql_fetch_assoc()"',
    'inurl:id= intext:"mysql_num_rows()"',
    'inurl:id= intext:"Warning: mysql_query()"',
    'inurl:id= intext:"mysqli_fetch_array()"',
    'inurl:cat= intext:"You have an error in your SQL syntax"',
    'inurl:page= intext:"You have an error in your SQL syntax"',
    'intext:"You have an error in your SQL syntax"',
    'intext:"mysql_fetch_array()"',
    'intext:"mysql_fetch_assoc()"',
    'intext:"Unclosed quotation mark"',
    'intext:"SQL syntax"',
    'intext:"PostgreSQL query failed"',
    'intext:"ORA-01756"',
    'intext:"Microsoft OLE DB Provider for SQL Server"',
    'intext:"Error Executing Database Query"',
    'filetype:php inurl:id=',
    'filetype:php inurl:cat=',
    'filetype:php inurl:page=',
    'filetype:php inurl:index.php?id=',
    'filetype:php inurl:product.php?id=',
    'filetype:php intext:"mysql_fetch_array()"',
    'filetype:php intext:"You have an error in your SQL syntax"',
    'inurl:.php?id=',
    'inurl:.php?cat=',
    'inurl:.php?page=',
    'inurl:.php?pid=',
    'inurl:.php?uid=',
]

SITE_DORK_TEMPLATES = [
    "site:{domain} inurl:admin",
    "site:{domain} inurl:login",
    "site:{domain} inurl:backup",
    "site:{domain} inurl:config",
    "site:{domain} inurl:id=",
    "site:{domain} inurl:index.php?id=",
    "site:{domain} inurl:product.php?id=",
    'site:{domain} intitle:"index of"',
    "site:{domain} filetype:sql",
    "site:{domain} filetype:env",
    "site:{domain} filetype:pdf",
    'site:{domain} intext:"password"',
    'site:{domain} intext:"You have an error in your SQL syntax"',
    'site:{domain} inurl:id= intext:"mysql_fetch_array()"',
]

KEYWORD_DORK_TEMPLATES = [
    "inurl:{keyword}",
    "intitle:{qkeyword}",
    "intext:{qkeyword}",
    'allintext:{qkeyword}',
    "{qkeyword}",
    'filetype:pdf {qkeyword}',
    'filetype:sql {qkeyword}',
    'filetype:env {qkeyword}',
    'inurl:admin {qkeyword}',
    'inurl:login {qkeyword}',
    'inurl:backup {qkeyword}',
    'intitle:"index of" {qkeyword}',
    'inurl:id= {qkeyword}',
    'inurl:cat= {qkeyword}',
    'inurl:index.php?id= {qkeyword}',
    'inurl:product.php?id= {qkeyword}',
    'filetype:php inurl:id= {qkeyword}',
    'inurl:id= intext:"mysql_fetch_array()" {qkeyword}',
    'inurl:id= intext:"You have an error in your SQL syntax" {qkeyword}',
]

SITE_KEYWORD_TEMPLATES = [
    "site:{domain} {qkeyword}",
    "site:{domain} inurl:admin {qkeyword}",
    "site:{domain} inurl:login {qkeyword}",
    "site:{domain} inurl:id= {qkeyword}",
    "site:{domain} inurl:index.php?id= {qkeyword}",
    "site:{domain} filetype:pdf {qkeyword}",
    "site:{domain} filetype:sql {qkeyword}",
    'site:{domain} intitle:"index of" {qkeyword}',
    'site:{domain} inurl:id= intext:"mysql_fetch_array()" {qkeyword}',
]


def quote_keyword(keyword: str) -> str:
    keyword = keyword.strip()
    if " " in keyword:
        return f'"{keyword}"'
    return keyword


def load_lines(path: Path, required: bool = True) -> list[str]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Fichier introuvable : {path}")
        return []

    lines = []
    seen = set()

    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip().lower()
        if not value or value.startswith("#") or value in seen:
            continue
        seen.add(value)
        lines.append(value)

    if required and not lines:
        raise ValueError(f"Aucune entrée trouvée dans {path}")

    return lines


def apply_domains(base_dorks: set[str], domains: list[str]) -> set[str]:
    if not domains:
        return set()

    site_dorks: set[str] = set()
    for domain in domains:
        for dork in base_dorks:
            site_dorks.add(f"site:{domain} {dork}")
        for template in SITE_DORK_TEMPLATES:
            site_dorks.add(template.format(domain=domain))
    return site_dorks


def generate_google_dorks(
    keywords: list[str],
    domains: list[str],
    include_site: bool = True,
) -> set[str]:
    dorks = set(PURE_GOOGLE_DORKS) | set(PURE_SQLI_DORKS)

    if include_site and domains:
        dorks.update(apply_domains(dorks, domains))

    for keyword in keywords:
        qkeyword = quote_keyword(keyword)
        for template in KEYWORD_DORK_TEMPLATES:
            dorks.add(template.format(keyword=keyword, qkeyword=qkeyword))

        if include_site and domains:
            for domain, template in product(domains, SITE_KEYWORD_TEMPLATES):
                dorks.add(template.format(domain=domain, keyword=keyword, qkeyword=qkeyword))

    return dorks


def generate_sqli_dorks(
    keywords: list[str],
    domains: list[str],
    include_site: bool = True,
) -> set[str]:
    dorks = set(PURE_SQLI_DORKS)

    for keyword in keywords:
        qkeyword = quote_keyword(keyword)
        sqli_keyword_templates = [
            "inurl:id= {qkeyword}",
            "inurl:cat= {qkeyword}",
            "inurl:page= {qkeyword}",
            "inurl:index.php?id= {qkeyword}",
            "inurl:product.php?id= {qkeyword}",
            "inurl:article.php?id= {qkeyword}",
            "allinurl:index.php?id= {qkeyword}",
            'inurl:id= intext:"mysql_fetch_array()" {qkeyword}',
            'inurl:id= intext:"You have an error in your SQL syntax" {qkeyword}',
            'filetype:php inurl:id= {qkeyword}',
            'filetype:php intext:"mysql_fetch_array()" {qkeyword}',
            'filetype:sql {qkeyword}',
            'filetype:env "DB_PASSWORD" {qkeyword}',
        ]
        for template in sqli_keyword_templates:
            dorks.add(template.format(qkeyword=qkeyword))

    if include_site and domains:
        for domain in domains:
            for dork in PURE_SQLI_DORKS:
                dorks.add(f"site:{domain} {dork}")
            for template in SITE_DORK_TEMPLATES:
                if "id=" in template or "sql" in template.lower() or "mysql" in template.lower():
                    dorks.add(template.format(domain=domain))
            for keyword in keywords:
                qkeyword = quote_keyword(keyword)
                for template in SITE_KEYWORD_TEMPLATES:
                    if "id=" in template or "mysql" in template or "sql" in template:
                        dorks.add(
                            template.format(domain=domain, keyword=keyword, qkeyword=qkeyword)
                        )

    return dorks


def generate_generic_dorks(
    keywords: list[str],
    domains: list[str],
    include_filetypes: bool = True,
    include_inurl: bool = True,
    include_intitle: bool = True,
    include_site: bool = True,
) -> set[str]:
    dorks = set(PURE_GOOGLE_DORKS)

    if include_filetypes:
        for ext in FILE_TYPES:
            dorks.add(f"filetype:{ext}")
            dorks.add(f'filetype:{ext} intext:password')

    if include_inurl:
        for pattern in INURL_PATTERNS:
            dorks.add(f"inurl:{pattern}")

    if include_intitle:
        for pattern in INTITLE_PATTERNS:
            dorks.add(f'intitle:"{pattern}"')

    for keyword in keywords:
        qkeyword = quote_keyword(keyword)
        for template in KEYWORD_DORK_TEMPLATES:
            dorks.add(template.format(keyword=keyword, qkeyword=qkeyword))

    if include_site and domains:
        dorks.update(apply_domains(dorks, domains))
        for keyword in keywords:
            qkeyword = quote_keyword(keyword)
            for domain, template in product(domains, SITE_KEYWORD_TEMPLATES):
                dorks.add(template.format(domain=domain, keyword=keyword, qkeyword=qkeyword))

    return dorks


def generate_dorks(
    keywords: list[str] | None = None,
    domains: list[str] | None = None,
    dork_types: list[str] | None = None,
    include_filetypes: bool = True,
    include_inurl: bool = True,
    include_intitle: bool = True,
    include_site: bool = True,
) -> set[str]:
    keywords = keywords or []
    domains = domains or []
    dork_types = dork_types or ["google"]

    types = set(dork_types or ["google"])
    dorks: set[str] = set()

    if "all" in types:
        dorks.update(generate_google_dorks(keywords, domains, include_site=include_site))
        dorks.update(
            generate_generic_dorks(
                keywords, domains,
                include_filetypes=include_filetypes,
                include_inurl=include_inurl,
                include_intitle=include_intitle,
                include_site=include_site,
            )
        )
        return dorks

    if "google" in types:
        dorks.update(generate_google_dorks(keywords, domains, include_site=include_site))

    if "sqli" in types:
        dorks.update(generate_sqli_dorks(keywords, domains, include_site=include_site))

    if "generic" in types:
        dorks.update(
            generate_generic_dorks(
                keywords, domains,
                include_filetypes=include_filetypes,
                include_inurl=include_inurl,
                include_intitle=include_intitle,
                include_site=include_site,
            )
        )

    return dorks


def to_google_url(dork: str) -> str:
    return GOOGLE_SEARCH_URL + quote_plus(dork)


def save_dorks(dorks: set[str], output_path: Path, as_urls: bool = False) -> None:
    lines = sorted(to_google_url(d) if as_urls else d for d in dorks)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère des Google dorks prêts à coller dans Google Search."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Fichier txt de keywords (optionnel si --pure)",
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
        default="google",
        help="Type : google (défaut), sqli, generic, all",
    )
    parser.add_argument(
        "--pure",
        action="store_true",
        help="Génère les dorks Google purs sans keywords",
    )
    parser.add_argument(
        "--urls",
        action="store_true",
        help="Exporte les URLs Google Search au lieu des dorks bruts",
    )
    parser.add_argument(
        "--no-filetypes",
        action="store_true",
        help="Désactive filetypes (generic)",
    )
    parser.add_argument(
        "--no-inurl",
        action="store_true",
        help="Désactive inurl (generic)",
    )
    parser.add_argument(
        "--no-intitle",
        action="store_true",
        help="Désactive intitle (generic)",
    )
    parser.add_argument(
        "--no-site",
        action="store_true",
        help="Désactive site:",
    )
    return parser.parse_args()


def run_generator(
    input_path: Path | None = None,
    output_path: Path | None = None,
    domains_path: Path | None = None,
    dork_types: list[str] | None = None,
    pure: bool = False,
    as_urls: bool = False,
    include_filetypes: bool = True,
    include_inurl: bool = True,
    include_intitle: bool = True,
    include_site: bool = True,
) -> tuple[int, Path]:
    dork_types = dork_types or ["google"]

    if output_path is None:
        suffix = dork_types[0]
        base = input_path.stem if input_path else "google"
        output_path = Path(f"{base}_{suffix}_dorks.txt")

    keywords: list[str] = []
    if input_path and not pure:
        keywords = load_lines(input_path, required=True)
        print(f"{len(keywords)} keywords chargés depuis {input_path}")
    elif pure:
        print("Mode pure : dorks Google sans keywords")

    domains = load_lines(domains_path, required=False) if domains_path else []
    print(f"Dorktype : {', '.join(dork_types)}")
    if domains:
        print(f"{len(domains)} domaines chargés depuis {domains_path}")

    dorks = generate_dorks(
        keywords=keywords,
        domains=domains,
        dork_types=dork_types,
        include_filetypes=include_filetypes,
        include_inurl=include_inurl,
        include_intitle=include_intitle,
        include_site=include_site and bool(domains),
    )
    save_dorks(dorks, output_path, as_urls=as_urls)

    format_label = "URLs Google" if as_urls else "dorks Google"
    print(f"{len(dorks)} {format_label} -> {output_path}")
    return len(dorks), output_path


def main() -> None:
    args = parse_args()

    if not args.pure and not args.input:
        print("Indique un fichier keywords ou utilise --pure", file=sys.stderr)
        sys.exit(1)

    try:
        run_generator(
            input_path=Path(args.input) if args.input else None,
            output_path=Path(args.output),
            domains_path=Path(args.domains) if args.domains else None,
            dork_types=[args.type],
            pure=args.pure,
            as_urls=args.urls,
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
