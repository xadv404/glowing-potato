#!/usr/bin/env python3
from pathlib import Path

# Dork templates by vulnerability category.
# {q} = keyword (quoted if multi-word by build_dork).
# Sources: GHDB 2026, SecOps, Box Piper, CVE advisories, DorkFinder.

# ── SQL Injection ──────────────────────────────────────────────────────────
SQLI_TEMPLATES = [
    # Tier 1: param + SQL error (highest signal)
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
    # Tier 1: DBMS-specific errors
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
    # Tier 2: CVE SQL 2026
    'inurl:"/api/action/datastore_search_sql" {q}',
    'inurl:"/user/login?_format=json" intext:"SQLSTATE" {q}',
    'inurl:"/jsonapi/node/" intext:"SQL" {q}',
    'inurl:"index.php?option=com_acym" intext:"sql" {q}',
    # Tier 2: classic GHDB PHP pages
    "inurl:index.php?id= {q}",
    "inurl:product.php?id= {q}",
    "inurl:article.php?id= {q}",
    "inurl:trainers.php?id= {q}",
    "inurl:buy.php?category= {q}",
    "inurl:games.php?id= {q}",
    "inurl:sql.php?id= {q}",
    "inurl:page.php?file= {q}",
    # Tier 3: SQL dumps / exposed files
    'filetype:sql intext:"phpMyAdmin SQL Dump" {q}',
    'filetype:sql "INSERT INTO" intext:"password" {q}',
    'ext:sql inurl:backup intext:"CREATE TABLE" {q}',
    'intitle:"index of" filetype:sql {q}',
    # Tier 3: condensed param combos
    'inurl:id= | inurl:cat= | inurl:page= intext:"SQL syntax" {q}',
    'inurl:id= | inurl:pid= | inurl:category= intext:"database error" {q}',
]

# ── Local File Inclusion (LFI) ─────────────────────────────────────────────
LFI_TEMPLATES = [
    'inurl:page= intext:"Warning: include" {q}',
    'inurl:file= intext:"Warning: include_once" {q}',
    'inurl:path= intext:"No such file or directory" {q}',
    'inurl:doc= intext:"open_basedir restriction" {q}',
    'inurl:page= intext:"failed to open stream" {q}',
    'inurl:include= intext:"Warning: include" {q}',
    'inurl:.php?page= intext:"warning: include" {q}',
    'inurl:.php?file= intext:"warning: require" {q}',
    'filetype:php inurl:page= intext:"include" {q}',
    'inurl:index.php?lang= {q}',
    'inurl:index.php?template= {q}',
    'inurl:view= intext:"Warning: include" {q}',
]

# ── Open Redirect ──────────────────────────────────────────────────────────
REDIRECT_TEMPLATES = [
    'inurl:redirect= inurl:.php {q}',
    'inurl:url= inurl:redirect {q}',
    'inurl:next= inurl:.php {q}',
    'inurl:return= inurl:.php {q}',
    'inurl:redirect_to= {q}',
    'inurl:dest= inurl:.php {q}',
    'inurl:goto= {q}',
    'inurl:target= inurl:.php {q}',
    'inurl:forward= inurl:.php {q}',
    'inurl:continue= inurl:login {q}',
]

# ── XSS ───────────────────────────────────────────────────────────────────
XSS_TEMPLATES = [
    'inurl:search= intext:"<script>" {q}',
    'inurl:q= intext:"<script>" {q}',
    'inurl:query= intext:"<script>" {q}',
    'inurl:search.php intext:"<script>alert" {q}',
    'inurl:message= intext:"<img src" {q}',
    'inurl:keyword= filetype:php {q}',
    'inurl:.php?s= intext:"<script>" {q}',
    'inurl:.php?term= {q}',
    'inurl:input= intext:"<script>" {q}',
    'inurl:comment= intext:"<script>" {q}',
]

# ── Admin Panels ───────────────────────────────────────────────────────────
ADMIN_TEMPLATES = [
    'intitle:"admin panel" inurl:admin {q}',
    'intitle:"admin login" {q}',
    'inurl:admin/login.php {q}',
    'inurl:adminpanel/ {q}',
    'inurl:wp-admin/ {q}',
    'intitle:"phpMyAdmin" {q}',
    'inurl:administrator/ {q}',
    'inurl:admin/index.php {q}',
    'intitle:"Plesk" inurl:8443 {q}',
    'intitle:"cPanel" inurl:2083 {q}',
    'inurl:cpanel/ {q}',
    'intitle:"Login" inurl:admin {q}',
    'inurl:dashboard/ intitle:"dashboard" {q}',
    'inurl:manage/ intitle:"manage" {q}',
]

# ── Config / Backup Exposure ───────────────────────────────────────────────
CONFIG_TEMPLATES = [
    'filetype:env intext:"DB_PASSWORD" {q}',
    'filetype:env intext:"SECRET_KEY" {q}',
    'filetype:cfg intext:"password" {q}',
    'filetype:ini intext:"password" {q}',
    'ext:bak inurl:config {q}',
    'ext:xml intext:"password" {q}',
    'intitle:"index of" inurl:config {q}',
    'intitle:"index of" filetype:log {q}',
    'filetype:log intext:"password" {q}',
    'intitle:"index of" ".env" {q}',
    'inurl:.git/config {q}',
    'intitle:"index of" ".git" {q}',
    'filetype:txt intext:"password" {q}',
    'ext:sql "INSERT INTO" intext:"users" {q}',
    'intitle:"index of" intext:"passwd" {q}',
    'filetype:yaml intext:"password" {q}',
    'filetype:json intext:"password" {q}',
    'intitle:"index of" "wp-config.php.bak" {q}',
]

# ── Category registry ──────────────────────────────────────────────────────
DORK_CATEGORIES: dict[str, list[str]] = {
    "sqli":     SQLI_TEMPLATES,
    "lfi":      LFI_TEMPLATES,
    "redirect": REDIRECT_TEMPLATES,
    "xss":      XSS_TEMPLATES,
    "admin":    ADMIN_TEMPLATES,
    "config":   CONFIG_TEMPLATES,
}

# Backward-compat aliases (imported by gui.py)
SQLI_HQ_TEMPLATES = SQLI_TEMPLATES
SQLI_SQL_TEMPLATES = SQLI_TEMPLATES

ALL_TEMPLATES: list[str] = [t for templates in DORK_CATEGORIES.values() for t in templates]


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
    categories: list[str] | None = None,
) -> list[str]:
    """Generate dorks for all keywords. Optionally restrict to specific categories."""
    if categories is not None:
        templates: list[str] = []
        for cat in categories:
            templates.extend(DORK_CATEGORIES.get(cat, []))
    else:
        templates = ALL_TEMPLATES

    dorks: list[str] = []
    for keyword in keywords:
        for template in templates:
            dorks.append(build_dork(keyword, template, domain))
    return dorks


def save_dorks(dorks: list[str], output_path: Path) -> None:
    output_path.write_text("\n".join(dorks) + "\n", encoding="utf-8")


def run_generator(
    input_path: Path,
    output_path: Path | None = None,
    domain: str | None = None,
    categories: list[str] | None = None,
) -> tuple[int, Path]:
    if output_path is None:
        stem = input_path.stem.removesuffix("_keywords")
        output_path = input_path.with_name(f"{stem}_dorks.txt")

    keywords = load_lines(input_path)
    dorks = generate_dorks(keywords, domain=domain, categories=categories)
    save_dorks(dorks, output_path)

    active_cats = categories or list(DORK_CATEGORIES.keys())
    total_tpl = sum(len(DORK_CATEGORIES[c]) for c in active_cats if c in DORK_CATEGORIES)
    print(
        f"{len(keywords)} keywords × {total_tpl} templates "
        f"({', '.join(active_cats)}) = {len(dorks)} dorks"
    )
    if domain:
        print(f"Domaine : {domain}")
    print(f"Sauvegardé : {output_path}")

    return len(dorks), output_path


if __name__ == "__main__":
    from gui import main as gui_main

    gui_main()
